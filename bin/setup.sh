#!/bin/bash

# Set up environment
RAVEN_HOME=~/Raven
echo "export RAVEN_HOME=$RAVEN_HOME" >> ~/.bash_profile
source "$HOME"/.bash_profile

yum install -y gcc make flex bison byacc cyrus-sasl-devel.x86_64 python3-devel
pip3 install --requirement requirements.txt

chmod -R 777 /tmp
hdfs dfs -chmod -R 777 /tmp
