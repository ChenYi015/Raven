#!/bin/bash
yum install -y git cyrus-sasl-devel.x86_64
pip install sasl thrift thrift-sasl pyhive presto-python-client
pip install --requirement requirements.txt
chmod -R 777 /tmp

# Using TPC-H kit for dataset generation
git clone https://github.com/gregrahn/tpch-kit /home/hadoop/
cd /home/hadoop/tpch-kit/dbgen && make
