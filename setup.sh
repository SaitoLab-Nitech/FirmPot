#!/bin/sh

# ----- Preparation -----

sudo apt-get update
sudo apt-get install -y wget git python3 python3-pip
pip3 install --upgrade pip
mkdir images
mkdir tools
cd tools

# ----- QEMU and Binfmt-misc -----

sudo apt install -y qemu-user qemu-user-static
sudo apt install -y binfmt-support
RESULT=`sudo /sbin/modprobe binfmt_misc`
if [ -n "$RESULT" ]; then
  echo "[-] Linux kernel may not specify support for binfmt_misc."
fi

# ----- Binwalk -----

# 1. Install binwalk
sudo apt install -y binwalk=2.2.0+dfsg1-1
#git clone https://github.com/ReFirmLabs/binwalk.git
#sudo apt install -y python3-distutils
#(cd binwalk && sudo python3 setup.py install)

# 2. Install sasquatch
sudo apt install -y zlib1g-dev liblzma-dev liblzo2-dev
git clone https://github.com/devttys0/sasquatch
(cd sasquatch && ./build.sh)

# 3. Install jefferson
sudo pip3 install cstruct
git clone https://github.com/sviehb/jefferson
(cd jefferson && sudo python3 setup.py install)

# 3. Install ubi_reader
sudo apt-get install -y liblzo2-dev
git clone https://github.com/jrspruitt/ubi_reader
(cd ubi_reader && sudo python3 setup.py install)

# ----- Selenium -----

# 1. Install web driver (Firefox)
wget https://github.com/mozilla/geckodriver/releases/download/v0.29.0/geckodriver-v0.29.0-linux64.tar.gz
tar zxvf geckodriver-v0.29.0-linux64.tar.gz
sudo mv geckodriver /usr/local/bin/

# 2. Install python module
pip3 install selenium-wire==2.1.2

# ----- Docker -----
<<COMMENT
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io
COMMENT
# ----- Python modules -----

pip3 install numpy tensorflow sklearn
pip3 install gensim==3.8 xxhash neologdn simstring-pure
pip3 install paramiko
pip3 install pandas flask dash pygeoip

# ----- Others -----

git clone https://github.com/mbcc2006/GeoLiteCity-data.git
cp GeoLiteCity-data/GeoLiteCity.dat ../utils/files/

# ----- End -----

cd -
