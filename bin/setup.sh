#!/bin/bash

# Set up environment
RAVEN_HOME=/home/hadoop/Raven
echo "export RAVEN_HOME=$RAVEN_HOME" >> /home/hadoop/.bash_profile

sudo yum install -y gcc make flex bison byacc cyrus-sasl-devel.x86_64 python3-devel
pip3 install --upgrade pip
pip3 install --requirement requirements.txt

sudo chmod -R 777 /tmp
