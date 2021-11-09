# FirmPot

## About FirmPot
FirmPot is a framework for the automatic generation of Intelligent-Interaction honeypots using OpenWrt-based firmware.
We presented FirmPot at CANDAR WICS 2021.

## Testing Environment
- OS: Ubuntu 20.04.2 LTS
- Kernel: Linux 5.8.0-48-generic x86_64
- CPU: Intel Core i7-10700K CPU@3.80GHz
- GPU: GeForce RTX 3060

## Files and Directories
```
FirmPot/
├── auto.py : Automatically generate a honeypot.
├── booter.py : Boot an embedded application from a firmware image
├── scanner.py : Scan the web application
├── learner.py : Learn the web interaction
├── manager.py : Create and manage the honeypot instance
├── honeypot.py : Program of honeypot server
├── analyzer.py : Analyze access logs observed honeypots 
├── setup.sh : Install required tools
├── honeypot_setup.sh : Install required tools for operation of honeypots
├── qemu-binfmt-conf.sh : Script to register configuration of binfmt_misc
├── README.md 
├── utils/ : Modules required by each program
├── images/ : Location of firmware images
├── tools/ : Tools required by each program
├── assets/ : Files used for visualization of log analysis
├── static/ : Files used for visualization of log analysis
├── templates/ : Files used for visualization of log analysis
└── demo/ : Demonstrations of honeypot generation by FirmPot
```

## Setup 
1. Clone this repository
```
$ git clone https://github.com/SaitoLab-Nitech/FirmPot.git 
```
2. Run `./setup.sh` script (require `sudo` password)
:::info
- Please comment out any tools that are already installed on your host
- If you get a comment, `[-] Linux kernel may not specify support for binfmt_misc.`, your kernel is not compatible with our programs
:::

## Preparetion
1. Download a firmware image from a vendor's website
2. Put the firmware image into `./images` directory
:::info
Our framework supports **OpenWrt** based firmware images. Please check your images before using our framework.
:::

## Usage
There are two patterns:
1. Generate a honeypot automatically
2. Generate a honeypot while checking each process
    - We prepare two demos : [demo1](./demo/demo1/demo1.md), [demo2](./demo/demo2/demo2.md)

### (Pattern 1) Generate a honeypot automatically./demo/demo1/demo1.md
1. Run `auto.py`
```
$ python3 auto.py <firmware image>
```
A honeypot instance (default: `./honeypot_instance/`) will be created.

2. Put the directory (`./honeypot_instance/`) on a public server
3. Go to the created directory of honeypot instance and launch the honeypot server
```
$ cd ./honeypot_instance/
$ sudo python3 honeypot.py or python3 honeypot.py -m
```
### (Pattern 2) Generate a honeypot while checking each process
1. Run `booter.py`
```
$ python3 booter.py <firmware images>
```
Multiple containers can be prepared by adding the `-c <number>` option. 
However, it may overload the host machine. 
`booter.py` will prompt you for the sudo password during execution.

2. Run `scanner.py`
```
$ python3 scanner.py -i <container's IPaddress>
```
3. Run `learner.py`
```
$ python3 learner.py
```
4. Run `manager.py`
```
$ python3 manager.py --create
```
5. Go to the created directory of honeypot instance (default: `./honeypot_instance/`) and launch the honeypot server
```
$ cd ./honeypot_instance/
$ python3 honeypot.py (or python3 honeypot.py -m)
```

## Log Analyze
Deployed honeypots will log access to them in the file (default: `./logs/access.log`).
The access log are visualized by running `analyzer.py`.
1. Run `analyzer.py`
```
$ python3 analyzer.py access1.log access2.log access3.log ...
```
2. Access to http://localhost:8050

## FAQ
### Failed to extract filesystem in `booter.py`.
Follow the checklist below to determine the cause.
1. The firmware may have been compressed in several layers. Try using the "unzip" or "untar" command to uncompress the file.
2. Try running booter.py with the `-m` option to recursively retrieve the file system.
3. Please check the version of binwalk. Make sure that binwalk is 2.2.* or earlier.
4. Please check that the firmware name does not contain any single-byte spaces. If the firmware name contains spaces, the program will not recognize it.

### Failed to launch the web application in `booter.py`.
The following checklist may help you solve this problem.
#### 1. Make sure you have configured binfmt_misc correctly
```
$ sudo su -
# cat /proc/sys/fs/binfmt_misc/qemu-(arch)
```
In additions, binfmt_misc can be used even after rebooting the host with the following configuration.

1. Move the `qemu-binfmt-conf.sh` in this repository to `/usr/local/bin/`
```
$ sudo chmod +x qemu-binfmt-conf.sh
$ sudo mv qemu-binfmt-conf.sh /usr/local/bin/qemu-binfmt-conf.sh
```
2. Create `/usr/local/bin/register.sh` and write the following
```
#!/bin/sh
QEMU_BIN_DIR=${QEMU_BIN_DIR:-/usr/bin}
if [ ! -d /proc/sys/fs/binfmt_misc ]; then
    echo "No binfmt support in the kernel."
    echo "  Try: '/sbin/modprobe binfmt_misc' from the host"
    exit 1
fi
if [ ! -f /proc/sys/fs/binfmt_misc/register ]; then
    mount binfmt_misc -t binfmt_misc /proc/sys/fs/binfmt_misc
fi
if [ "${1}" = "--reset" ]; then
    shift
    find /proc/sys/fs/binfmt_misc -type f -name 'qemu-*' -exec sh -c 'echo -1 > {}' \;
fi
exec /usr/local/bin/qemu-binfmt-conf.sh --qemu-suffix "-static" --qemu-path "${QEMU_BIN_DIR}" $@
```
3. Change the permission
```
$ sudo chmod +x /usr/local/bin/register.sh
```
4. Create `/etc/systemd/system/register.service` and write the following
```
[Unit]
Description= register cpu emulator
[Service]
ExecStart = /usr/local/bin/register.sh
Restart = no
Type = simple
RemainAfterExit=yes
[Install]
WantedBy = multi-user.target
```

5. Start the daemon
```
$ sudo systemctl daemon-reload
$ sudo systemctl enable register.service
$ sudo systemctl start register.service 
$ sudo systemctl status register.service
```
:::info
The openwrt MIPS firmware has a special magic number. If it fails to execute, please execute the following command.
```
$ sudo su -
## ↓ This is MIPS little endian 
# echo ':qemu-xmmipsel:M::\x7f\x45\x4c\x46\x01\x01\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x08\x00:\xff\xff\xff\xff\xff\xff\xff\x00\xff\xff\xff\xff\xff\xff\xff\xff\xfe\xff\xff\xff:/usr/bin/qemu-mipsel-static:' > /proc/sys/fs/binfmt_misc/register

## ↓ This is MIPS big endian 
# echo ':qemu-xmmips:M::\x7f\x45\x4c\x46\x01\x02\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x08:\xff\xff\xff\xff\xff\xff\xff\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xfe\xff\xff:/usr/bin/qemu-mips-static:' > /proc/sys/fs/binfmt_misc/register
```
:::

#### 2. There are some SSL-related failures, which can be resolved by tweaking the configuration file
#### 3. Try to change the permissions of the extracted file system
```
$ sudo chmod -R 777　./extracted_fs 
or
$ sudo chmod -R 755 ./extracted_fs/bin ./extracted_fs/lib
```
#### 4. Possibility of QEMU's errors
```
$ sudo chroot extracted_fs/ /bin/busybox
qemu: uncaught target signal 4 (Illegal instruction) - core dumped
Illegal instruction
```
I'm sorry, our current framework does not support this.

#### 5. Possibility of Openwrt's errors or Luci's errors
I'm sorry, our current framework does not support this.


### Cannot login to the web application in `scanner.py`.
- Some web applications may output a dialog before you enter your password. In this case, you have to turn off the dialog manually.
- Normally, you will be asked to set a default password to login to the web. You can manually set a password in advance. Set the same password as the one written in the params file.

### Cannot crawl the web application in `scanner.py`.
- Two types of crawlers are available. Please use the flag to switch between them.
```
# line 119 in `scanner.py`
atag_list, url_list, crawled_list = crawling(driver, ip, atag_list, url_list, crawled_list, flag=False) # <= If the crawling fails, try setting the flag to True
```

### Learning model does not converge or learning model is unable to interact
- Adjust the training parameters for both Seq2Seq and Word2Vec in `utils/params.py`.
- The Word2Vec model can be created in advance using `utils/word2vec.py`. Please specify the word2vec model to `learner.py`.
```
$ python3 utils/word2vec.py -l honeypot/learning.db
# Generate word2vec.bin in ./honeypot/
$ python3 learner.py -w honeypot/word2vec.bin
```