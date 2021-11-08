#!/bin/bash

yum install -y git gcc make flex bison byacc cyrus-sasl-devel.x86_64 python3-devel
pip3 install --requirement requirements.txt
chmod -R 777 /tmp

# Using TPC-H kit for dataset generation
git clone https://github.com/gregrahn/tpch-kit /home/hadoop/
cd /home/hadoop/tpch-kit/dbgen &&

# SSB
