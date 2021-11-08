#!/bin/bash

yum install -y gcc make flex bison byacc cyrus-sasl-devel.x86_64 python3-devel
pip3 install --requirement requirements.txt
chmod -R 777 /tmp

# Using TPC-H kit for dataset generation
git clone https://github.com/gregrahn/tpch-kit /home/hadoop/tpch-kit

# SSB

# Spark 指定 Hive 作为 metastore
cp /etc/hadoop/conf/core-site.xml /etc/hadoop/conf/hdfs-site.xml /etc/spark/conf
cp /etc/hive/conf/hive-site.xml /etc/spark/conf