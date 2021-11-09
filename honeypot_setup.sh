#!/bin/sh

# ----- Preparation -----

sudo apt-get update
sudo apt-get install -y python3 python3-pip
pip3 install --upgrade pip

# ----- Python modules -----

sudo pip3 install numpy tensorflow sklearn
sudo pip3 install gensim==3.8 xxhash neologdn simstring-pure

