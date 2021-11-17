# Copyright 2021 Raven Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json
import logging
import os
import random
import string
from datetime import datetime
from pprint import pprint
from typing import List

import boto3
import botocore.exceptions

from tools import ssh_exec_commands


class Provider:

    def __init__(self, config: dict):
        self._name = 'Amazon Web Service'
        self._region = config['Properties']['Region']
        self._key_name = config['Properties']['KeyName']
        self._session = boto3.session.Session(region_name=self._region)

    @property
    def name(self):
        return self._name

    def create_stack(self, stack_name: str, filename: str, tags=None):
        """
        Create stack by AWS CloudFormation template.
        :param stack_name: The name of the stack.
        :param filename: The name of CloudFormation template file.
        :param tags: The tags of stack.
        :return:
        """
        # 1. Create CloudFormation client
        client = self._session.client('cloudformation')

        # 2. Read CloudFormation template from file.
        with open(os.path.join(os.environ['RAVEN_HOME'], 'configs', 'providers', 'aws', filename),
                  encoding='utf-8') as file:
            template_body = file.read()

        # 3. Create stack
        try:
            logging.info(f'Creating stack {stack_name}...')
            response = client.create_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Capabilities=['CAPABILITY_NAMED_IAM'],
                Tags=tags if tags else []
            )
            waiter = client.get_waiter('stack_create_complete')
            waiter.wait(StackName=stack_name)
            logging.info(f'Stack {stack_name} has been created.')
            logging.info(f'StackId: {response["StackId"]}')
        except botocore.exceptions.ClientError as error:
            if error.response['Fail']['Code'] == 'AlreadyExistsException':
                logging.error(f'Stack {stack_name} already exists.')
            else:
                logging.error(error.response)

    def describe_stack(self):
        # TODO
        pass

    def delete_stack(self, stack_name: str):
        client = self._session.client('cloudformation')
        client.delete_stack(StackName=stack_name)

    def create_emr_stack_for_engine(self, engine: str, tags=None) -> (str, str):
        """
        Create AWS EMR cluster for engine.
        :param engine: The name of engine, allowed values are hive, spark-sql, presto.
        :param tags: The tags of AWS EMR cluster.
        :return: The stack name and AWS EMR cluster ID.
        """
        logging.info(f'Creating EMR cluster for {engine.capitalize()}...')
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        stack_name = f'EMR-Raven-Stack-for-{engine.capitalize()}-{random_suffix}'
        filename = f'emr-cloudformation-for-{engine}.yaml'
        self.create_stack(stack_name=stack_name, filename=filename, tags=tags if tags else [])

        client = self._session.client('cloudformation')
        logical_resource_id = 'EMRCluster'
        response = client.describe_stack_resource(StackName=stack_name, LogicalResourceId=logical_resource_id)
        cluster_id = response['StackResourceDetail']['PhysicalResourceId']
        response = self.describe_emr(cluster_id)
        try:
            output_dir = os.path.join(os.environ['RAVEN_HOME'], 'out', f'emr_{cluster_id}')
            os.makedirs(output_dir)
            with open(os.path.join(output_dir, 'cluster.info'), mode='w', encoding='utf-8') as file:
                file.write(f'Stack Name: {stack_name}\n')
                file.write('Cluster info: \n')
                pprint(response['Cluster'], stream=file, indent=2)

        except OSError as error:
            logging.error(error)

        logging.info(f'AWS has finished creating EMR cluster, cluster id: {cluster_id}.')
        return stack_name, cluster_id

    def setup_emr_master_with_commands(self, cluster_id: str, commands: List[str]):
        """
        Setup AWS EMR
        :param commands: Commands for setting up EMR cluster nodes.
        :param cluster_id: The ID of AWS EMR Cluster.
        :return:
        """
        logging.info(f'AWS is setting up EMR cluster master nodes with id: {cluster_id}...')
        if commands is None:
            commands = []
        master_ips = self.get_emr_master_public_ips(cluster_id=cluster_id)
        for hostname in master_ips:
            ssh_exec_commands(
                hostname=hostname,
                commands=commands,
                key_name=self._key_name
            )
        logging.info(f'AWS has finished setting up EMR cluster master nodes.')

    def setup_emr_core_with_commands(self, cluster_id: str, commands: List[str]):
        """
        Setup AWS EMR
        :param commands: Commands for setting up EMR cluster nodes.
        :param cluster_id: The ID of AWS EMR Cluster.
        :return:
        """
        logging.info(f'AWS is setting up EMR cluster core nodes with id: {cluster_id}...')
        if commands is None:
            commands = []
        core_ips = self.get_emr_core_public_ips(cluster_id=cluster_id)
        for hostname in core_ips:
            ssh_exec_commands(
                hostname=hostname,
                commands=commands,
                key_name=self._key_name
            )
        logging.info(f'AWS has finished setting up EMR cluster core nodes.')

    def setup_emr_with_commands(self, cluster_id: str, commands: List[str]):
        """
        Setup AWS EMR
        :param commands: Commands for setting up EMR cluster nodes.
        :param cluster_id: The ID of AWS EMR Cluster.
        :return:
        """
        logging.info(f'AWS is setting up EMR cluster with id: {cluster_id}...')
        if commands is None:
            commands = []
        master_ips = self.get_emr_master_public_ips(cluster_id=cluster_id)
        core_ips = self.get_emr_core_public_ips(cluster_id=cluster_id)
        for hostname in master_ips + core_ips:
            logging.info(f'AWS has finished setting up EMR cluster.')
            ssh_exec_commands(
                hostname=hostname,
                commands=commands,
                key_name=self._key_name
            )

    def create_and_setup_emr_for_engine(self, engine: str, tags=None) -> str:
        """
        Create and setup AWS EMR cluster for engine.
        :param engine: The name of engine, allowed values are hive, spark_sql, presto.
        :param tags: The tags of AWS EMR cluster.
        :return: The ID of AWS EMR cluster.
        """
        _, cluster_id = self.create_emr_stack_for_engine(engine=engine, tags=tags if tags else [])

        self.setup_emr_with_commands(
            cluster_id=cluster_id,
            commands=[
                'sudo yum install -y amazon-cloudwatch-agent',
                'sudo mkdir -p /usr/share/collectd',
                'sudo touch /usr/share/collectd/types.db',
                'aws s3 cp s3://olapstorage/configs/amazon-cloudwatch-agent.json /home/hadoop',
                'sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:/home/hadoop/amazon-cloudwatch-agent.json',
                'sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -m ec2 -a status'
            ]
        )

        self.setup_emr_master_with_commands(
            cluster_id=cluster_id,
            commands=[
                'sudo yum install -y git',
                f'git clone https://github.com/ChenYi015/Raven.git /home/hadoop/Raven',
                'cd /home/hadoop/Raven; git checkout dev; chmod u+x bin/setup.sh; bin/setup.sh'
            ]
        )
        return cluster_id

    def describe_emr(self, cluster_id: str) -> dict:
        # TODO
        client = self._session.client('emr')
        response = client.describe_cluster(
            ClusterId=cluster_id
        )
        return response

    def monitor_emr(self, cluster_id: str, start: datetime, end: datetime):
        """
        Monitor AWS EMR cluster and write metrics into files.
        :param cluster_id: The ID of AWS EMR cluster.
        :param start: The start timestamp.
        :param end: The end timestamp.
        :return:
        """
        logging.info(f'AWS is monitoring EMR cluster, cluster_id: {cluster_id}...')
        output_dir = os.path.join(os.environ['RAVEN_HOME'], 'out', f'emr_{cluster_id}', 'metrics')
        try:
            os.makedirs(output_dir)
        except OSError as error:
            logging.error(error)
        self.get_emr_master_metrics(cluster_id=cluster_id, start=start, end=end, output_dir=output_dir)
        self.get_emr_core_metrics(cluster_id=cluster_id, start=start, end=end, output_dir=output_dir)
        logging.info(f'AWS has finished monitoring EMR cluster.')

    def delete_emr(self, cluster_id: str):
        # TODO
        pass

    def get_emr_master_public_ips(self, cluster_id):
        """
        Get public IPs of AWS EMR Master nodes.
        :param cluster_id: The id of AWS EMR cluster.
        :return:
        """
        client = self._session.client('ec2')
        response = client.describe_instances(
            Filters=[
                {
                    'Name': 'tag:aws:elasticmapreduce:job-flow-id',
                    'Values': [cluster_id]
                },
                {
                    'Name': 'tag:aws:elasticmapreduce:instance-group-role',
                    'Values': ['MASTER']
                }
            ]
        )

        master_public_ips = [instance['PublicIpAddress'] for instance in response['Reservations'][0]['Instances']]
        return master_public_ips

    def get_emr_core_public_ips(self, cluster_id):
        """
        Get public IPs of AWS EMR Core nodes.
        :param cluster_id: The id of AWS EMR cluster.
        :return:
        """
        client = self._session.client('ec2')
        response = client.describe_instances(
            Filters=[
                {
                    'Name': 'tag:aws:elasticmapreduce:job-flow-id',
                    'Values': [cluster_id]
                },
                {
                    'Name': 'tag:aws:elasticmapreduce:instance-group-role',
                    'Values': ['CORE']
                }
            ]
        )

        core_public_ips = [instance['PublicIpAddress'] for instance in response['Reservations'][0]['Instances']]
        return core_public_ips

    def get_emr_master_metrics(self, cluster_id: str, start: datetime = None,
                               end: datetime = None, output_dir: str = None) -> List[dict]:
        """
        Get metrics from AWS CloudWatchAgent and write into files.
        :param cluster_id: The AWS EMR cluster id.
        :param start: The start timestamp.
        :param end: The end timestamp.
        :param output_dir:
        :return:
        """
        client = self._session.client('ec2')
        response = client.describe_instances(
            Filters=[
                {
                    'Name': 'tag:aws:elasticmapreduce:job-flow-id',
                    'Values': [cluster_id]
                },
                {
                    'Name': 'tag:aws:elasticmapreduce:instance-group-role',
                    'Values': ['MASTER']
                }
            ]
        )
        metrics = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                if instance['State']['Name'] == 'running':
                    instance_id = instance['InstanceId']
                    metric = self.get_ec2_metrics(instance, start, end)
                    if output_dir:
                        with open(os.path.join(output_dir, f'master_{instance_id}.metrics'), mode='w',
                                  encoding='utf-8') as file:
                            pprint(metric, stream=file, indent=2)
                    metrics.append(metric)
        return metrics

    def get_emr_core_metrics(self, cluster_id: str, start: datetime = None, end: datetime = None,
                             output_dir: str = None) -> List[dict]:
        """
        Get metrics from AWS CloudWatchAgent and write into files.
        :param cluster_id: The AWS EMR cluster id.
        :param start: The start timestamp.
        :param end: The end timestamp.
        :param output_dir:
        :return:
        """
        client = self._session.client('ec2')
        response = client.describe_instances(
            Filters=[
                {
                    'Name': 'tag:aws:elasticmapreduce:job-flow-id',
                    'Values': [cluster_id]
                },
                {
                    'Name': 'tag:aws:elasticmapreduce:instance-group-role',
                    'Values': ['CORE']
                }
            ]
        )
        metrics = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                if instance['State']['Name'] == 'running':
                    instance_id = instance['InstanceId']
                    response = self.get_ec2_metrics(instance, start, end)
                    metric = response['MetricDataResults']
                    if output_dir:
                        with open(os.path.join(output_dir, f'core_{instance_id}.metrics'), mode='w',
                                  encoding='utf-8') as file:
                            pprint(metric, stream=file, indent=2)
                    metrics.append(metric)
        return metrics

    def get_ec2_metrics(self, instance: dict, start: datetime, end: datetime) -> dict:
        """
        Get metrics from AWS CloudWatchAgent by instance.
        :param instance:
        :param start:
        :param end:
        :return:
            {
                'Id': 'string',
                'Label': 'string',
                'Timestamps': [
                    datetime(2015, 1, 1),
                ],
                'Values': [
                    123.0,
                ],
                'StatusCode': 'Complete'|'InternalError'|'PartialData',
                'Messages': [
                    {
                        'Code': 'string',
                        'Value': 'string'
                    },
                ]
            }
        """

        client = self._session.client('cloudwatch')

        with open(os.path.join(os.environ['RAVEN_HOME'], 'configs', 'providers', 'aws',
                               'cloudwatch-metric-data-queries-for-m5-xlarge.json'), mode='r', encoding="utf-8") as _:
            metric_data_queries = json.load(_)

        for metric_data_query in metric_data_queries:
            metric_data_query['MetricStat']['Metric']['Dimensions'].append({
                'Name': 'InstanceId',
                'Value': instance['InstanceId']
            })
            metric_data_query['MetricStat']['Metric']['Dimensions'].append({
                'Name': 'ImageId',
                'Value': instance['ImageId']
            })
            metric_data_query['MetricStat']['Metric']['Dimensions'].append({
                'Name': 'InstanceType',
                'Value': instance['InstanceType']
            })

        try:
            response = client.get_metric_data(
                MetricDataQueries=metric_data_queries,
                StartTime=start,
                EndTime=end
            )
            return response
        except botocore.exceptions.ClientError as error:
            logging.error(error.response)
        except KeyError as error:
            logging.error(error)

    # AWS Cost Explorer
    def get_cost_and_usage(self, ):
        # TODO
        pass
