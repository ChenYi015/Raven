#!/bin/bash

sudo yum install -y git gcc make flex bison byacc cyrus-sasl-devel.x86_64 python38 python38-pip python38-devel
ln -s /usr/bin/pip-3.8 /usr/bin/pip3
pip3 install --requirement "$RAVEN_HOME"/configs/engines/athena/requirements.txt
