#!/bin/bash

yum install -y git gcc make flex bison byacc cyrus-sasl-devel.x86_64 python3-devel amazon-cloudwatch-agent

# Install and start AWS CloudWatch agent
aws s3 cp s3://olapstorage/configs/amazon-cloudwatch-agent.json /home/hadoop/
mkdir -p /usr/share/collectd
touch /usr/share/collectd/types.db
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:/home/hadoop/amazon-cloudwatch-agent.json

# Setup Raven
RAVEN_HOME=/home/hadoop/Raven
git clone https://github.com/ChenYi015/Raven.git $RAVEN_HOME
echo "export RAVEN_HOME=$RAVEN_HOME" | tee -a /home/hadoop/.bash_profile
source /home/hadoop/.bash_profile

chmod -R 777 /tmp
hdfs dfs -chmod -R 777 /tmp
