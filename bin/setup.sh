#!/bin/bash

# Set up environment
RAVEN_HOME="$HOME"/Raven
echo "export RAVEN_HOME=$RAVEN_HOME" >> "$HOME"/.bash_profile

sudo yum install -y gcc make flex bison byacc cyrus-sasl-devel.x86_64 python3-devel
sudo pip3 install --upgrade pip setuptools
sudo ln -s /usr/local/bin/pip3 /usr/bin/pip3
pip install --index-url https://mirrors.aliyun.com/pypi/simple/ pypandoc
pip3 install --requirement requirements.txt

sudo chmod -R 777 /tmp
