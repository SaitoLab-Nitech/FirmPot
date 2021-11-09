
#------------------------------------------------
# Import
#------------------------------------------------

import os
import sys
sys.dont_write_bytecode = True
import argparse

# My program
from utils.utils import *
from utils.params import boot_params, docker_config

#------------------------------------------------
# Parameters
#------------------------------------------------

# Support Services
support_services = [
    "http",
    "ssh",
    "dropbear",
    "telnet"
]

# The linux filesystem to find
basic_linuxfs = [
    "bin",
    "sbin",
    "etc",
    "www"
]

# Words in non-executable files
exclude_words = [
    "network",
    "led",
    "init",
    "switch",
    "system",
    "fstab",
    "usb",
    "firewall",
    "iptv",
    "security",
    "nat",
    "wireless",
    "dns",
    "vpn",
    "watchdog",
    "uci",
    "wifi",
    "avahi",
]

#------------------------------------------------
# Functions
#------------------------------------------------

def get_dirs(path):
    """Return a list of directories under the <path>."""
    return run_cmd('ls -d "' + path + '"*/')

def is_linuxfs(path):
    """Return a boolean whether the directory of <path> matches the structure of the Linux filesystem."""
    dirlist = run_cmd('ls -1 ' + path)
    if len(list(set(basic_linuxfs) & set(dirlist))):
        return True
    else:
        return False


def is_openwrt(path):
    """Returns a boolean whether the directory of <path> is openwrt-based by checking for openwrt-related files."""
    result = run_cmd('find ' + path + ' -name "*openwrt*"')
    if len(result):
        return True
    else:
        return False

def copy_qemu(path, arch, bit, endian):
    """Copy the qemu-user-static binary to a <path> that matches the CPU <arch>itecture, <bit>,  and <endian>."""

    if "ARM" in arch:
        if "32" in bit:
            if "LSB" in endian:
                run_cmd("cp /usr/bin/qemu-arm-static " + path + "/usr/bin/") # (ARM, 32, little)            
            elif "MSB" in endian:
                run_cmd("cp /usr/bin/qemu-armeb-static " + path + "/usr/bin/") # (ARM, 32, big)
        elif "64" in bit:
            if "LSB" in endian:
                run_cmd("cp /usr/bin/qemu-aarch64-static " + path + "/usr/bin/") # (ARM, 64, little)  
            elif "MSB" in endian:
                run_cmd("cp /usr/bin/qemu-aarch64_be-static " + path + "/usr/bin/") # (ARM, 64, big)   

    if "MIPS" in arch:
        if "32" in bit:
            if "LSB" in endian:
                run_cmd("cp /usr/bin/qemu-mipsel-static " + path + "/usr/bin/") # (MIPS, 32, little)
            elif "MSB" in endian:
                run_cmd("cp /usr/bin/qemu-mips-static " + path + "/usr/bin/")  # (MIPS, 32, big)
        elif "64" in bit:
            if "LSB" in endian:
                run_cmd("cp /usr/bin/qemu-mips64el-static " + path + "/usr/bin/") # (MIPS, 64, little)
            elif "MSB" in endian:
                run_cmd("cp /usr/bin/qemu-mips64-static " + path + "/usr/bin/") # (MIPS, 64, big)

    if "PowerPC" in arch:
        if "32" in bit:
            if "MSB" in endian:
                run_cmd("cp /usr/bin/qemu-ppc-static " + path + "/usr/bin/")  # (PPC, 32, big)               
        elif "64" in bit:
            if "MSB" in endian:
                run_cmd("cp /usr/bin/qemu-ppc64-static " + path + "/usr/bin/") # (PPC, 64, big)

    if "Intel" in arch:
        if "32" in bit:
            run_cmd("cp /usr/bin/qemu-i386-static " + path + "/usr/bin/")  # (Intel 80386, 32, -)               


def create_startup(dir_path, startup_path):
    """Create a startup script to <startup_path> by parsing /etc/rc.d/ in the directory of <dir_path>."""

    startup_list = run_cmd('ls -1 ' + dir_path + '/etc/rc.d | grep ^S')
    for word in exclude_words:
        startup_list = [item for item in startup_list if word not in item] 

    # Search service
    service_list = [s for s in startup_list if service in s]

    if len(service_list) == 0:
        print("[-] Could not find any %s services." % service)
        sys.exit(0)
    elif len(service_list) == 1:
        launch_service = service_list[0]
        print("[*] One service found :", launch_service)
    else:
        print("[!] Some services found :", service_list)
        while True:
            print("[?] Which service do you want to start? Please enter a number.")
            print(" / ".join([str(i) + " : " + s for i, s in enumerate(service_list)]))
            choice = input('Enter number: ')
            choice = int(choice)
            if choice in [i for i in range(len(service_list))]:
                launch_service = service_list[choice]
                break
            else:
                print("[-] The number you entered is incorrect.")
        print("[*] Launch :", launch_service)

    with open(startup_path, 'w') as f:
        f.writelines("#!/bin/sh\n")
        f.writelines("mkdir /var/lock\n")
        f.writelines("mkdir /var/run\n")
        f.writelines("/sbin/ubusd &\n")
        f.writelines("/sbin/procd &\n")
        for s in startup_list:
            f.writelines("/etc/rc.d/" + s + " start\n")
            if s == launch_service:
                break

        f.writelines("/bin/ash\n")

    run_cmd("sudo chmod 777 " + startup_path)

def run_containers(container_num, docker_config):
    """Run as many containers as the number of <container_num> according to the setting of <docker_config>."""

    for i in range(container_num):

        # Create a docker network
        subnet = docker_config["ip_1st_octet"] + "." + str(int(docker_config["ip_2nd_octet"])+i) + "." + docker_config["ip_3rd_octet"] + "." + docker_config["ip_4th_octet"] + docker_config["subnet_mask"]
        cmd = 'sudo docker network create --driver=bridge --subnet=' + subnet + ' ' + docker_config["network_name"] + str(i)
        run_cmd(cmd)

        # Create a docker container
        cmd = 'sudo docker run -itd --privileged --net=' + docker_config["network_name"] + str(i) + ' --name=' + docker_config["container_name"] + str(i) + " " + docker_config["image_name"]
        print("[*] Run :", cmd)
        run_cmd(cmd)

    success_list = []
    failure_list = []
    ip_list = []
    for i in range(container_num):
        container_name =  docker_config["container_name"] + str(i)
        cmd = "sudo docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' " + container_name
        result = run_cmd(cmd)

        if len(result) > 0:
            success_list.append(container_name)
            ip_list.append(result[0])
        else:
            failure_list.append(container_name)

    print("[*] Finished!")

    if len(success_list) > 0:
        print("[*] Success: ", success_list)
    if len(failure_list) > 0:
        print("[-] Failure: ", failure_list)

    if len(ip_list) > 0 and service == "http":
        print("[*] List of Accessible IP Address (HTTP)")
        print(' '.join(["http://" + ip for ip in ip_list]))
        print("")
        print("[*] List of Accessible IP Address (HTTPS)")
        print(' '.join(["https://" + ip for ip in ip_list]))

    elif len(ip_list) > 0:
        print("[*] List of Accessible IP Address")
        print(' '.join([ip for ip in ip_list]))


#------------------------------------------------
# Main
#------------------------------------------------

def main():
    
    # [1] Extract Filesystem
    if not os.path.exists(dir_path):
        extracted_path = "/".join(firmware_path.split("/")[:-1]) + "/_" + firmware_path.split('/')[-1] + ".extracted/"
        if extracted_path.startswith("/"):
            extracted_path = "." + extracted_path

        if os.path.exists(extracted_path):
            print("[!] Do not run binwalk because the extracted results are already there.")
            print("[!] If you want to run binwalk, delete", extracted_path)
        else: # If the extraction is complete, pass the following process.
            print("[*] Try to extract filesystem from", firmware_path)
            if is_matryoshka:
                run_cmd("binwalk -eM " + firmware_path)
            else:
                run_cmd("binwalk -e " + firmware_path)
        
        dirlist = get_dirs(extracted_path)
        
        linuxfs = ""
        while len(dirlist) > 0: 
            check_dir = dirlist.pop(0)
            if is_linuxfs(check_dir):
                linuxfs = check_dir
                break
            else:
                dirlist.extend(get_dirs(check_dir))
            
        if len(linuxfs) == 0:
            print("[-] Failed to extract a filesystem.")
            sys.exit(0)
        else:
            print("[*] Success to extract :", linuxfs)
            run_cmd("cp -r " + check_dir + " " + dir_path)

    # [2] Check whether the OpenWrt-based firmware
    if is_openwrt(dir_path):
        print("[*] The extracted filesystem is OpenWrt-based.")
    else:
        print("[-] The extracted filesystem is not OpenWrt-based.")
        sys.exit(0)
      
    # [3] Check architecture
    arch = run_cmd("file " + dir_path + "/bin/busybox | awk '{print $6}'")
    bit = run_cmd("file " + dir_path + "/bin/busybox | awk '{print $3}'")
    endian = run_cmd("file " + dir_path + "/bin/busybox | awk '{print $4}'")
    print("[*] Arch :", arch, "Bit :", bit, "Endian :", endian)

    # [4] Copy QEMU binary
    copy_qemu(dir_path, arch[0], bit[0], endian[0])
    print("[*] Copy QEMU user-mode binary to the filesystem")

	# [5] Create new startup script
    if not os.path.exists(startup_path):
        create_startup(dir_path, startup_path)
        print("[*] Generate new startup script.")

    # [6] Create a Dockerfile
    run_cmd('echo "FROM scratch" > Dockerfile')
    run_cmd('echo "ADD ' + dir_path + ' /" >> Dockerfile')
    run_cmd('echo "COPY ' + startup_path + ' /" >> Dockerfile')
    run_cmd("echo 'CMD ["+ '"./' + startup_path.split('/')[-1] + '"]' + "' >> Dockerfile")

    # [7] Build a docker image
    run_cmd('sudo docker build -t ' + docker_config["image_name"] + ' .')

    # [8] Run docker containers
    if container_num == 0:
        print("[*] Finished!")
    else:
        run_containers(container_num, docker_config)

#------------------------------------------------
#  if __name__ == '__main__':
#------------------------------------------------

if __name__ == '__main__':

    # Argument Parser
    parser = argparse.ArgumentParser(description='Boot an embedded application from a firmware image.')
    parser.add_argument('firmware', help="Specify the path to the firmware image.")
    parser.add_argument('-f', '--filesystem', default=boot_params["filesystem"], help="Specify the directory name/path where the file system extracted from the firmware image is saved (default: '%s')."%boot_params["filesystem"])
    parser.add_argument('-s', '--startup', default=boot_params["startup"], help="Specify the path of the new startup script to be created, or the name of the startup script that exists, if any (default: '%s')."%boot_params["startup"])
    parser.add_argument('-c', '--containers', default=1, type=int, help="Specify the number of containers to be launched, or 0 if you don't want to launch any (default: 1).")
    parser.add_argument('-m', '--matryoshka', action='store_true', help="Use binwalk's recursive filesystem search feature (not used by default).")
    parser.add_argument('--service', default="http", help="Specify the service you want to start from [http, ssh, telnet] (default is '%s')." % support_services[0])
    args = parser.parse_args() 

    # ----- Check Arguments -----

    # Path to firmware image
    firmware_path = args.firmware
    if not os.path.exists(firmware_path):
        print("[-] The path to the firmware image is incorrect.")
        sys.exit(0)

    # Path to filesystem extracted from the firmware image
    dir_path = args.filesystem
    if os.path.exists(dir_path):
        if len(os.listdir(dir_path))!= 0:
            print("[!] There are already files in %s." % dir_path)
            print("[?] Do you want to stop extracting the firmware and use %s?" % dir_path)
            if yes_no_input():
                print("[*] Use %s to boot." % dir_path)
            else:
                print("[-] Empty the directory or delete the directory, and try again.")
                sys.exit(0)

    # Path to startup script
    startup_path = args.startup
    if os.path.exists(startup_path):
        print("[!] The %s already exists." % startup_path)
        print("[?] Do you want to use %s to boot the firmware?" % startup_path)
        if yes_no_input():
            print("[*] Use %s to boot." % startup_path)
        else:
            print("[-] Delete %s or move it to another location, and try again." % startup_path)
            sys.exit(0)

    # Number of containers to run
    container_num = args.containers

    if os.path.exists("./Dockerfile"):
        print("[!] There are already ./Dockerfile")
        print("[?] Can this file be overwritten?")
        if not yes_no_input():
            print("[-] Delete ./Dockerfile or move it to another location, and try again.")
            sys.exit(0)

    # Flag of binwalk
    is_matryoshka = args.matryoshka

    # Launch service
    service = args.service
    if service not in support_services:
        print("[-] The specified string is wrong.")
        print("[-] Please specify the service from :", support_services)
        sys.exit(0)

    main()

