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
import os
import random
import string
from datetime import datetime
from pprint import pprint
from typing import List, Optional

import boto3
import botocore.exceptions

import configs
from tools import ssh_exec_commands

logger = configs.ROOT_LOGGER


class Provider:

    def __init__(self, config: dict):
        self.name = 'Amazon Web Service'
        self._region = config['Properties']['Region']
        self._key_name = config['Properties']['KeyName']
        self._session = boto3.session.Session(region_name=self._region)

    def exists_stack(self, stack_name: str) -> bool:
        """
        Test whether stack with specified name exists.
        :param stack_name: Name of stack.
        :return:
        """
        if self._wait_stack_exists(stack_name=stack_name):
            logger.info(f'Stack [{stack_name}] already exists.')
            return True
        else:
            logger.info(f'Stack [{stack_name}] does not exist.')
            return False

    def create_stack(self, stack_name: str, template_body: str, tags=None, **kwargs):
        """
                Create stack by AWS CloudFormation template.
                :param stack_name: The name of the stack.
                :param template_body: Cloudformation template.
                :param tags: The tags of stack.
                :return:
                """
        # Create CloudFormation client
        if self.exists_stack(stack_name=stack_name):
            return

        # Create stack
        logger.info(f'Creating stack [{stack_name}]...')
        parameters = []
        for key, value in kwargs.items():
            parameters.append(
                {
                    'ParameterKey': key,
                    'ParameterValue': value
                }
            )
        try:
            client = self._session.client('cloudformation')
            response = client.create_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Capabilities=['CAPABILITY_NAMED_IAM'],
                Tags=tags if tags else [],
                Parameters=parameters
            )
            logger.info(f'Waiting for stack [{stack_name}] creation to complete...')
            self._wait_stack_create_complete(stack_name=stack_name)
            logger.info(f'Stack [{stack_name}] has been created.')
        except botocore.exceptions.ClientError as error:
            logger.error(error.response['Error']['Message'])

    def describe_stack(self, stack_name: str) -> Optional[dict]:
        client = self._session.client('cloudformation')
        try:
            response = client.describe_stacks(
                StackName=stack_name
            )
            return response
        except botocore.exceptions.ValidationError as error:
            logger.error(error.with_traceback())

    def get_stack_output_by_key(self, stack_name, output_key: str) -> Optional[str]:
        # Stack outputs is like:
        #
        # 'Outputs': [
        #                 {
        #                     'OutputKey': 'string',
        #                     'OutputValue': 'string',
        #                     'Description': 'string',
        #                     'ExportName': 'string'
        #                 },
        #             ]
        response = self.describe_stack(stack_name=stack_name)
        outputs = response['Stacks'][0]['Outputs']
        for output in outputs:
            if output['OutputKey'] == output_key:
                return output['OutputValue']

    def delete_stack(self, stack_name: str):
        logger.info(f'Deleting stack [{stack_name}]...')
        if not self.exists_stack(stack_name=stack_name):
            return
        client = self._session.client('cloudformation')
        client.delete_stack(StackName=stack_name)
        self._wait_stack_delete_complete(stack_name=stack_name)

    def create_emr_stack_for_engine(self, engine: str = 'all', tags=None, *, install_cwa: bool = False) -> (str, str):
        """
        Create AWS EMR cluster for engine.
        :param install_cwa:
        :param engine: The name of engine, allowed values are hive, spark-3.1.1-sql, presto-0.266.1.
        :param tags: The tags of AWS EMR cluster.
        :return: The stack name and AWS EMR cluster ID.
        """
        logger.info(f'AWS is creating EMR cluster for {engine.capitalize()}...')
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        stack_name = f'EMR-Raven-Stack-for-{engine.capitalize()}-{random_suffix}'
        if engine == 'all':
            filename = 'cloudformation-template.yaml'
        else:
            filename = f'{engine}-cloudformation.yaml'
        with open(os.path.join(os.environ['RAVEN_HOME'], 'configs', 'providers', 'aws', 'emr', filename),
                  encoding='utf-8') as file:
            template_body = file.read()
        self.create_stack(stack_name=stack_name, template_body=template_body, tags=tags if tags else [])

        client = self._session.client('cloudformation')
        logical_resource_id = 'EMRCluster'
        response = client.describe_stack_resource(StackName=stack_name, LogicalResourceId=logical_resource_id)
        cluster_id = response['StackResourceDetail']['PhysicalResourceId']
        response = self.describe_emr(cluster_id)
        try:
            output_dir = os.path.join(os.environ['RAVEN_HOME'], 'out', f'emr_{cluster_id}')
            os.makedirs(output_dir, exist_ok=True)
            with open(os.path.join(output_dir, 'cluster.info'), mode='w', encoding='utf-8') as file:
                file.write(f'Stack Name: {stack_name}\n')
                file.write('Cluster info: \n')
                pprint(response['Cluster'], stream=file, indent=2)

        except OSError as error:
            logger.error(error)

        if install_cwa:
            self.setup_emr_with_commands(
                cluster_id=cluster_id,
                commands=[
                    'sudo yum install -y amazon-cloudwatch-agent',
                    'sudo mkdir -p /usr/share/collectd',
                    'sudo touch /usr/share/collectd/types.db',
                    'aws s3 cp s3://olapstorage/configs/amazon-cloudwatch-agent.json /home/hadoop-2.10.1',
                    'sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:/home/hadoop-2.10.1/amazon-cloudwatch-agent.json',
                    'sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -m ec2 -a status'
                ]
            )

        self.setup_emr_master_with_commands(
            cluster_id=cluster_id,
            commands=[
                'sudo yum install -y git',
                f'git clone {configs.GITHUB_REPO_URL} /home/hadoop-2.10.1/Raven',
                'cd /home/hadoop-2.10.1/Raven; git checkout dev; chmod u+x bin/setup.sh; bin/setup.sh'
            ]
        )

        logger.info(f'AWS has finished creating EMR cluster, cluster id: {cluster_id}.')

        return stack_name, cluster_id

    def create_ec2_stack_for_athena(self, tags=None) -> (str, str):
        """
        Create AWS EC2 instance for engine.
        :param tags: The tags of AWS EMR cluster.
        :return: AWS EC2 ID and public ip.
        """
        logger.info(f'AWS is creating EC2 instance for Athena...')
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        stack_name = f'Raven-Stack-for-Athena-{random_suffix}'
        with open(os.path.join(os.environ['RAVEN_HOME'], 'configs', 'providers', 'aws', 'athena-cloudformation.yaml'),
                  encoding='utf-8') as file:
            template_body = file.read()
        self.create_stack(stack_name=stack_name, template_body=template_body, tags=configs.TAGS)
        instance_id = self.get_stack_output_by_key(stack_name=stack_name, output_key='EC2InstanceID')
        public_ip = self.get_stack_output_by_key(stack_name=stack_name, output_key='EC2InstancePublicIP')
        logger.info(f'AWS has finished creating EC2 instance, instance id: {instance_id}, public ip: {public_ip}.')
        ssh_exec_commands(

        )

    def setup_ec2_with_commands(self, instance_id: str, commands: List[str]):
        """
        Setup AWS EC2 instance.
        :param commands: Commands.
        :param instance_id: The ID of AWS EC2 Instance.
        """
        logger.info(f'AWS is setting up EC2 instance [{instance_id}]...')
        if commands is None:
            commands = []
        # TODO
        # ssh_exec_commands(
        #     hostname=hostname,
        #     commands=commands,
        #     key_name=self._key_name
        # )
        logger.info(f'AWS has finished setting up EMR cluster.')

    def setup_emr_master_with_commands(self, cluster_id: str, commands: List[str]):
        """
        Setup AWS EMR
        :param commands: Commands for setting up EMR cluster nodes.
        :param cluster_id: The ID of AWS EMR Cluster.
        :return:
        """
        logger.info(f'AWS is setting up EMR cluster master nodes, cluster id: {cluster_id}...')
        if commands is None:
            commands = []
        master_ips = self.get_emr_master_public_ips(cluster_id=cluster_id)
        for hostname in master_ips:
            ssh_exec_commands(
                hostname=hostname,
                commands=commands,
                key_name=self._key_name
            )
        logger.info(f'AWS has finished setting up EMR cluster master nodes.')

    def setup_emr_core_with_commands(self, cluster_id: str, commands: List[str]):
        """
        Setup AWS EMR
        :param commands: Commands for setting up EMR cluster nodes.
        :param cluster_id: The ID of AWS EMR Cluster.
        :return:
        """
        logger.info(f'AWS is setting up EMR cluster core nodes with id: {cluster_id}...')
        if commands is None:
            commands = []
        core_ips = self.get_emr_core_public_ips(cluster_id=cluster_id)
        for hostname in core_ips:
            ssh_exec_commands(
                hostname=hostname,
                commands=commands,
                key_name=self._key_name
            )
        logger.info(f'AWS has finished setting up EMR cluster core nodes.')

    def setup_emr_with_commands(self, cluster_id: str, commands: List[str]):
        """
        Setup AWS EMR
        :param commands: Commands for setting up EMR cluster nodes.
        :param cluster_id: The ID of AWS EMR Cluster.
        :return:
        """
        logger.info(f'AWS is setting up EMR cluster with id: {cluster_id}...')
        if commands is None:
            commands = []
        master_ips = self.get_emr_master_public_ips(cluster_id=cluster_id)
        core_ips = self.get_emr_core_public_ips(cluster_id=cluster_id)
        for hostname in master_ips + core_ips:
            ssh_exec_commands(
                hostname=hostname,
                commands=commands,
                key_name=self._key_name
            )
            logger.info(f'AWS has finished setting up EMR cluster.')

    def create_and_setup_emr_for_engine(self, engine: str, tags=None) -> str:
        """
        Create and setup AWS EMR cluster for engine.
        :param engine: The name of engine, allowed values are hive, spark_sql, presto-0.266.1.
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
                'aws s3 cp s3://olapstorage/configs/amazon-cloudwatch-agent.json /home/hadoop-2.10.1',
                'sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:/home/hadoop-2.10.1/amazon-cloudwatch-agent.json',
                'sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -m ec2 -a status'
            ]
        )

        self.setup_emr_master_with_commands(
            cluster_id=cluster_id,
            commands=[
                'sudo yum install -y git',
                f'git clone https://github.com/ChenYi015/Raven.git /home/hadoop-2.10.1/Raven',
                'cd /home/hadoop-2.10.1/Raven; git checkout dev; chmod u+x bin/setup.sh; bin/setup.sh'
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
        :param start: The run timestamp.
        :param end: The end timestamp.
        :return:
        """
        logger.info(f'AWS is monitoring EMR cluster, cluster_id: {cluster_id}...')
        output_dir = os.path.join(os.environ['RAVEN_HOME'], 'out', f'emr_{cluster_id}', 'metrics')
        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as error:
            logger.error(error)
        self.get_emr_master_metrics(cluster_id=cluster_id, start=start, end=end, output_dir=output_dir)
        self.get_emr_core_metrics(cluster_id=cluster_id, start=start, end=end, output_dir=output_dir)
        logger.info(f'AWS has finished monitoring EMR cluster.')

    def delete_emr(self, cluster_id: str):
        # TODO
        pass

    def monitor_kylin4_ec2_cluster(self, master_instance_id: str, start: datetime, end: datetime):
        """
        Monitor AWS EMR cluster and write metrics into files.
        :param master_instance_id: The instance id of Kylin4 master node.
        :param start: The run timestamp.
        :param end: The end timestamp.
        :return:
        """
        logger.info(f'AWS is monitoring Kylin4 EC2 cluster, master instance id: {master_instance_id}...')
        output_dir = os.path.join(os.environ['RAVEN_HOME'], 'out', f'ec2_{master_instance_id}', 'metrics')
        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as error:
            logger.error(error)
        with open(os.path.join(os.environ['RAVEN_HOME'], 'out', f'ec2_{master_instance_id}',
                               'cluster_info.json')) as file:
            cluster_info = json.load(file)
        metric = self.get_kylin4_ec2_metrics(master_instance_id, start, end)
        with open(os.path.join(output_dir, f'master_{master_instance_id}.metrics'), mode='w',
                  encoding='utf-8') as file:
            pprint(metric, stream=file, indent=2)
        for slave in cluster_info['Slaves']:
            metric = self.get_kylin4_ec2_metrics(instance_id=slave['InstanceId'], start=start, end=end)
            with open(os.path.join(output_dir, f'slave_{slave["InstanceId"]}.metrics'), mode='w',
                      encoding='utf-8') as file:
                pprint(metric, stream=file, indent=2)
        logger.info(f'AWS has finished monitoring Kylin4 EC2 cluster.')



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
                               end: datetime = None, output_dir: str = None) -> list:
        """
        Get metrics from AWS CloudWatchAgent and write into files.
        :param cluster_id: The AWS EMR cluster id.
        :param start: The run timestamp.
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
                instance_id = instance['InstanceId']
                metric = self.get_ec2_metrics(instance, start, end)
                if output_dir:
                    with open(os.path.join(output_dir, f'master_{instance_id}.metrics'), mode='w',
                              encoding='utf-8') as file:
                        pprint(metric, stream=file, indent=2)
                        # file.write(json.dumps(metric, encoding='utf-8'))
                metrics.append(metric)
        return metrics

    def get_emr_core_metrics(self, cluster_id: str, start: datetime = None, end: datetime = None,
                             output_dir: str = None) -> List[dict]:
        """
        Get metrics from AWS CloudWatchAgent and write into files.
        :param cluster_id: The AWS EMR cluster id.
        :param start: The run timestamp.
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
                instance_id = instance['InstanceId']
                response = self.get_ec2_metrics(instance, start, end)
                metric = response['MetricDataResults']
                if output_dir:
                    with open(os.path.join(output_dir, f'core_{instance_id}.metrics'), mode='w',
                              encoding='utf-8') as file:
                        pprint(metric, stream=file, indent=2)
                        # file.write(json.dumps(metric, encoding='utf-8'))
                metrics.append(metric)
        return metrics

    def get_ec2_metrics(self, instance: dict, start: datetime, end: datetime) -> list:
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
                               'cloudwatch-metric-data-queries-for-m5-xlarge.json'), encoding="utf-8") as _:
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
            logger.error(error.response)
        except KeyError as error:
            logger.error(error)

    def get_kylin4_ec2_metrics(self, instance_id: str, start: datetime, end: datetime) -> list:
        """
        Get metrics from AWS CloudWatchAgent by instance.
        :param instance_id:
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
                               'cloudwatch-metric-data-queries-for-m5-xlarge.json'), encoding="utf-8") as _:
            metric_data_queries = json.load(_)

        for metric_data_query in metric_data_queries:
            metric_data_query['MetricStat']['Metric']['Dimensions'].append({
                'Name': 'InstanceId',
                'Value': instance_id
            })
            metric_data_query['MetricStat']['Metric']['Dimensions'].append({
                'Name': 'ImageId',
                'Value': 'ami-07191cf2912e097a6'
            })
            metric_data_query['MetricStat']['Metric']['Dimensions'].append({
                'Name': 'InstanceType',
                'Value': 'm5.xlarge'
            })

        try:
            response = client.get_metric_data(
                MetricDataQueries=metric_data_queries,
                StartTime=start,
                EndTime=end
            )
            return response
        except botocore.exceptions.ClientError as error:
            logger.error(error.response)
        except KeyError as error:
            logger.error(error)

    # AWS Cost Explorer
    def get_cost_and_usage(self, ):
        # TODO
        pass

    def _wait_stack_create_complete(self, stack_name: str) -> bool:
        client = self._session.client('cloudformation')
        waiter = client.get_waiter('stack_create_complete')
        try:
            waiter.wait(StackName=stack_name)
            return True
        except botocore.exceptions.WaiterError as error:
            logger.error(error.last_response['Error']['Message'])
        return False

    def _wait_stack_delete_complete(self, stack_name: str) -> bool:
        client = self._session.client('cloudformation')
        waiter = client.get_waiter('stack_delete_complete')
        try:
            waiter.wait(StackName=stack_name)
            return True
        except botocore.exceptions.WaiterError as error:
            logger.error(error.last_response['Error']['Message'])
        return False

    def _wait_rollback_complete(self, stack_name: str) -> bool:
        client = self._session.client('cloudformation')
        waiter = client.get_waiter('stack_rollback_complete')
        try:
            waiter.wait(StackName=stack_name)
            return True
        except botocore.exceptions.WaiterError as error:
            logger.error(error.last_response['Error']['Message'])
        return False

    def _wait_update_complete(self, stack_name: str) -> bool:
        client = self._session.client('cloudformation')
        waiter = client.get_waiter('stack_update_complete')
        try:
            waiter.wait(StackName=stack_name)
            return True
        except botocore.exceptions.WaiterError as error:
            logger.error(error.last_response['Error']['Message'])
        return False

    def _wait_stack_exists(self, stack_name: str) -> bool:
        client = self._session.client('cloudformation')
        waiter = client.get_waiter('stack_exists')
        try:
            waiter.wait(
                StackName=stack_name,
                WaiterConfig={
                    'Delay': 3,
                    'MaxAttempts': 1
                }
            )
            return True
        except botocore.exceptions.WaiterError as error:
            logger.error(error.last_response['Error']['Message'])
        return False

    def describe_ec2_instances(self, instance_ids: list) -> dict:
        """
        Describe AWS EC2 instance.
        Detailed documentation: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_instances
        Response Syntax:
        {
            'Reservations': [
                {
                    'Groups': [
                        {
                            'GroupName': 'string',
                            'GroupId': 'string'
                        },
                    ],
                    'Instances': [
                        {
                            'AmiLaunchIndex': 123,
                            'ImageId': 'string',
                            'InstanceId': 'string',
                            'InstanceType': 't1.micro'|'t2.nano'|'t2.micro'|'t2.small'|'t2.medium'|'t2.large'|'t2.xlarge'|'t2.2xlarge'|'t3.nano'|'t3.micro'|'t3.small'|'t3.medium'|'t3.large'|'t3.xlarge'|'t3.2xlarge'|'t3a.nano'|'t3a.micro'|'t3a.small'|'t3a.medium'|'t3a.large'|'t3a.xlarge'|'t3a.2xlarge'|'t4g.nano'|'t4g.micro'|'t4g.small'|'t4g.medium'|'t4g.large'|'t4g.xlarge'|'t4g.2xlarge'|'m1.small'|'m1.medium'|'m1.large'|'m1.xlarge'|'m3.medium'|'m3.large'|'m3.xlarge'|'m3.2xlarge'|'m4.large'|'m4.xlarge'|'m4.2xlarge'|'m4.4xlarge'|'m4.10xlarge'|'m4.16xlarge'|'m2.xlarge'|'m2.2xlarge'|'m2.4xlarge'|'cr1.8xlarge'|'r3.large'|'r3.xlarge'|'r3.2xlarge'|'r3.4xlarge'|'r3.8xlarge'|'r4.large'|'r4.xlarge'|'r4.2xlarge'|'r4.4xlarge'|'r4.8xlarge'|'r4.16xlarge'|'r5.large'|'r5.xlarge'|'r5.2xlarge'|'r5.4xlarge'|'r5.8xlarge'|'r5.12xlarge'|'r5.16xlarge'|'r5.24xlarge'|'r5.metal'|'r5a.large'|'r5a.xlarge'|'r5a.2xlarge'|'r5a.4xlarge'|'r5a.8xlarge'|'r5a.12xlarge'|'r5a.16xlarge'|'r5a.24xlarge'|'r5b.large'|'r5b.xlarge'|'r5b.2xlarge'|'r5b.4xlarge'|'r5b.8xlarge'|'r5b.12xlarge'|'r5b.16xlarge'|'r5b.24xlarge'|'r5b.metal'|'r5d.large'|'r5d.xlarge'|'r5d.2xlarge'|'r5d.4xlarge'|'r5d.8xlarge'|'r5d.12xlarge'|'r5d.16xlarge'|'r5d.24xlarge'|'r5d.metal'|'r5ad.large'|'r5ad.xlarge'|'r5ad.2xlarge'|'r5ad.4xlarge'|'r5ad.8xlarge'|'r5ad.12xlarge'|'r5ad.16xlarge'|'r5ad.24xlarge'|'r6g.metal'|'r6g.medium'|'r6g.large'|'r6g.xlarge'|'r6g.2xlarge'|'r6g.4xlarge'|'r6g.8xlarge'|'r6g.12xlarge'|'r6g.16xlarge'|'r6gd.metal'|'r6gd.medium'|'r6gd.large'|'r6gd.xlarge'|'r6gd.2xlarge'|'r6gd.4xlarge'|'r6gd.8xlarge'|'r6gd.12xlarge'|'r6gd.16xlarge'|'x1.16xlarge'|'x1.32xlarge'|'x1e.xlarge'|'x1e.2xlarge'|'x1e.4xlarge'|'x1e.8xlarge'|'x1e.16xlarge'|'x1e.32xlarge'|'i2.xlarge'|'i2.2xlarge'|'i2.4xlarge'|'i2.8xlarge'|'i3.large'|'i3.xlarge'|'i3.2xlarge'|'i3.4xlarge'|'i3.8xlarge'|'i3.16xlarge'|'i3.metal'|'i3en.large'|'i3en.xlarge'|'i3en.2xlarge'|'i3en.3xlarge'|'i3en.6xlarge'|'i3en.12xlarge'|'i3en.24xlarge'|'i3en.metal'|'hi1.4xlarge'|'hs1.8xlarge'|'c1.medium'|'c1.xlarge'|'c3.large'|'c3.xlarge'|'c3.2xlarge'|'c3.4xlarge'|'c3.8xlarge'|'c4.large'|'c4.xlarge'|'c4.2xlarge'|'c4.4xlarge'|'c4.8xlarge'|'c5.large'|'c5.xlarge'|'c5.2xlarge'|'c5.4xlarge'|'c5.9xlarge'|'c5.12xlarge'|'c5.18xlarge'|'c5.24xlarge'|'c5.metal'|'c5a.large'|'c5a.xlarge'|'c5a.2xlarge'|'c5a.4xlarge'|'c5a.8xlarge'|'c5a.12xlarge'|'c5a.16xlarge'|'c5a.24xlarge'|'c5ad.large'|'c5ad.xlarge'|'c5ad.2xlarge'|'c5ad.4xlarge'|'c5ad.8xlarge'|'c5ad.12xlarge'|'c5ad.16xlarge'|'c5ad.24xlarge'|'c5d.large'|'c5d.xlarge'|'c5d.2xlarge'|'c5d.4xlarge'|'c5d.9xlarge'|'c5d.12xlarge'|'c5d.18xlarge'|'c5d.24xlarge'|'c5d.metal'|'c5n.large'|'c5n.xlarge'|'c5n.2xlarge'|'c5n.4xlarge'|'c5n.9xlarge'|'c5n.18xlarge'|'c5n.metal'|'c6g.metal'|'c6g.medium'|'c6g.large'|'c6g.xlarge'|'c6g.2xlarge'|'c6g.4xlarge'|'c6g.8xlarge'|'c6g.12xlarge'|'c6g.16xlarge'|'c6gd.metal'|'c6gd.medium'|'c6gd.large'|'c6gd.xlarge'|'c6gd.2xlarge'|'c6gd.4xlarge'|'c6gd.8xlarge'|'c6gd.12xlarge'|'c6gd.16xlarge'|'c6gn.medium'|'c6gn.large'|'c6gn.xlarge'|'c6gn.2xlarge'|'c6gn.4xlarge'|'c6gn.8xlarge'|'c6gn.12xlarge'|'c6gn.16xlarge'|'c6i.large'|'c6i.xlarge'|'c6i.2xlarge'|'c6i.4xlarge'|'c6i.8xlarge'|'c6i.12xlarge'|'c6i.16xlarge'|'c6i.24xlarge'|'c6i.32xlarge'|'cc1.4xlarge'|'cc2.8xlarge'|'g2.2xlarge'|'g2.8xlarge'|'g3.4xlarge'|'g3.8xlarge'|'g3.16xlarge'|'g3s.xlarge'|'g4ad.xlarge'|'g4ad.2xlarge'|'g4ad.4xlarge'|'g4ad.8xlarge'|'g4ad.16xlarge'|'g4dn.xlarge'|'g4dn.2xlarge'|'g4dn.4xlarge'|'g4dn.8xlarge'|'g4dn.12xlarge'|'g4dn.16xlarge'|'g4dn.metal'|'cg1.4xlarge'|'p2.xlarge'|'p2.8xlarge'|'p2.16xlarge'|'p3.2xlarge'|'p3.8xlarge'|'p3.16xlarge'|'p3dn.24xlarge'|'p4d.24xlarge'|'d2.xlarge'|'d2.2xlarge'|'d2.4xlarge'|'d2.8xlarge'|'d3.xlarge'|'d3.2xlarge'|'d3.4xlarge'|'d3.8xlarge'|'d3en.xlarge'|'d3en.2xlarge'|'d3en.4xlarge'|'d3en.6xlarge'|'d3en.8xlarge'|'d3en.12xlarge'|'dl1.24xlarge'|'f1.2xlarge'|'f1.4xlarge'|'f1.16xlarge'|'m5.large'|'m5.xlarge'|'m5.2xlarge'|'m5.4xlarge'|'m5.8xlarge'|'m5.12xlarge'|'m5.16xlarge'|'m5.24xlarge'|'m5.metal'|'m5a.large'|'m5a.xlarge'|'m5a.2xlarge'|'m5a.4xlarge'|'m5a.8xlarge'|'m5a.12xlarge'|'m5a.16xlarge'|'m5a.24xlarge'|'m5d.large'|'m5d.xlarge'|'m5d.2xlarge'|'m5d.4xlarge'|'m5d.8xlarge'|'m5d.12xlarge'|'m5d.16xlarge'|'m5d.24xlarge'|'m5d.metal'|'m5ad.large'|'m5ad.xlarge'|'m5ad.2xlarge'|'m5ad.4xlarge'|'m5ad.8xlarge'|'m5ad.12xlarge'|'m5ad.16xlarge'|'m5ad.24xlarge'|'m5zn.large'|'m5zn.xlarge'|'m5zn.2xlarge'|'m5zn.3xlarge'|'m5zn.6xlarge'|'m5zn.12xlarge'|'m5zn.metal'|'h1.2xlarge'|'h1.4xlarge'|'h1.8xlarge'|'h1.16xlarge'|'z1d.large'|'z1d.xlarge'|'z1d.2xlarge'|'z1d.3xlarge'|'z1d.6xlarge'|'z1d.12xlarge'|'z1d.metal'|'u-6tb1.56xlarge'|'u-6tb1.112xlarge'|'u-9tb1.112xlarge'|'u-12tb1.112xlarge'|'u-6tb1.metal'|'u-9tb1.metal'|'u-12tb1.metal'|'u-18tb1.metal'|'u-24tb1.metal'|'a1.medium'|'a1.large'|'a1.xlarge'|'a1.2xlarge'|'a1.4xlarge'|'a1.metal'|'m5dn.large'|'m5dn.xlarge'|'m5dn.2xlarge'|'m5dn.4xlarge'|'m5dn.8xlarge'|'m5dn.12xlarge'|'m5dn.16xlarge'|'m5dn.24xlarge'|'m5dn.metal'|'m5n.large'|'m5n.xlarge'|'m5n.2xlarge'|'m5n.4xlarge'|'m5n.8xlarge'|'m5n.12xlarge'|'m5n.16xlarge'|'m5n.24xlarge'|'m5n.metal'|'r5dn.large'|'r5dn.xlarge'|'r5dn.2xlarge'|'r5dn.4xlarge'|'r5dn.8xlarge'|'r5dn.12xlarge'|'r5dn.16xlarge'|'r5dn.24xlarge'|'r5dn.metal'|'r5n.large'|'r5n.xlarge'|'r5n.2xlarge'|'r5n.4xlarge'|'r5n.8xlarge'|'r5n.12xlarge'|'r5n.16xlarge'|'r5n.24xlarge'|'r5n.metal'|'inf1.xlarge'|'inf1.2xlarge'|'inf1.6xlarge'|'inf1.24xlarge'|'m6g.metal'|'m6g.medium'|'m6g.large'|'m6g.xlarge'|'m6g.2xlarge'|'m6g.4xlarge'|'m6g.8xlarge'|'m6g.12xlarge'|'m6g.16xlarge'|'m6gd.metal'|'m6gd.medium'|'m6gd.large'|'m6gd.xlarge'|'m6gd.2xlarge'|'m6gd.4xlarge'|'m6gd.8xlarge'|'m6gd.12xlarge'|'m6gd.16xlarge'|'m6a.large'|'m6a.xlarge'|'m6a.2xlarge'|'m6a.4xlarge'|'m6a.8xlarge'|'m6a.12xlarge'|'m6a.16xlarge'|'m6a.24xlarge'|'m6a.32xlarge'|'m6a.48xlarge'|'m6i.large'|'m6i.xlarge'|'m6i.2xlarge'|'m6i.4xlarge'|'m6i.8xlarge'|'m6i.12xlarge'|'m6i.16xlarge'|'m6i.24xlarge'|'m6i.32xlarge'|'mac1.metal'|'x2gd.medium'|'x2gd.large'|'x2gd.xlarge'|'x2gd.2xlarge'|'x2gd.4xlarge'|'x2gd.8xlarge'|'x2gd.12xlarge'|'x2gd.16xlarge'|'x2gd.metal'|'vt1.3xlarge'|'vt1.6xlarge'|'vt1.24xlarge'|'im4gn.16xlarge'|'im4gn.2xlarge'|'im4gn.4xlarge'|'im4gn.8xlarge'|'im4gn.large'|'im4gn.xlarge'|'is4gen.2xlarge'|'is4gen.4xlarge'|'is4gen.8xlarge'|'is4gen.large'|'is4gen.medium'|'is4gen.xlarge'|'g5g.xlarge'|'g5g.2xlarge'|'g5g.4xlarge'|'g5g.8xlarge'|'g5g.16xlarge'|'g5g.metal'|'g5.xlarge'|'g5.2xlarge'|'g5.4xlarge'|'g5.8xlarge'|'g5.12xlarge'|'g5.16xlarge'|'g5.24xlarge'|'g5.48xlarge',
                            'KernelId': 'string',
                            'KeyName': 'string',
                            'LaunchTime': datetime(2015, 1, 1),
                            'Monitoring': {
                                'State': 'disabled'|'disabling'|'enabled'|'pending'
                            },
                            'Placement': {
                                'AvailabilityZone': 'string',
                                'Affinity': 'string',
                                'GroupName': 'string',
                                'PartitionNumber': 123,
                                'HostId': 'string',
                                'Tenancy': 'default'|'dedicated'|'host',
                                'SpreadDomain': 'string',
                                'HostResourceGroupArn': 'string'
                            },
                            'Platform': 'Windows',
                            'PrivateDnsName': 'string',
                            'PrivateIpAddress': 'string',
                            'ProductCodes': [
                                {
                                    'ProductCodeId': 'string',
                                    'ProductCodeType': 'devpay'|'marketplace'
                                },
                            ],
                            'PublicDnsName': 'string',
                            'PublicIpAddress': 'string',
                            'RamdiskId': 'string',
                            'State': {
                                'Code': 123,
                                'Name': 'pending'|'running'|'shutting-down'|'terminated'|'stopping'|'stopped'
                            },
                            'StateTransitionReason': 'string',
                            'SubnetId': 'string',
                            'VpcId': 'string',
                            'Architecture': 'i386'|'x86_64'|'arm64'|'x86_64_mac',
                            'BlockDeviceMappings': [
                                {
                                    'DeviceName': 'string',
                                    'Ebs': {
                                        'AttachTime': datetime(2015, 1, 1),
                                        'DeleteOnTermination': True|False,
                                        'Status': 'attaching'|'attached'|'detaching'|'detached',
                                        'VolumeId': 'string'
                                    }
                                },
                            ],
                            'ClientToken': 'string',
                            'EbsOptimized': True|False,
                            'EnaSupport': True|False,
                            'Hypervisor': 'ovm'|'xen',
                            'IamInstanceProfile': {
                                'Arn': 'string',
                                'Id': 'string'
                            },
                            'InstanceLifecycle': 'spot'|'scheduled',
                            'ElasticGpuAssociations': [
                                {
                                    'ElasticGpuId': 'string',
                                    'ElasticGpuAssociationId': 'string',
                                    'ElasticGpuAssociationState': 'string',
                                    'ElasticGpuAssociationTime': 'string'
                                },
                            ],
                            'ElasticInferenceAcceleratorAssociations': [
                                {
                                    'ElasticInferenceAcceleratorArn': 'string',
                                    'ElasticInferenceAcceleratorAssociationId': 'string',
                                    'ElasticInferenceAcceleratorAssociationState': 'string',
                                    'ElasticInferenceAcceleratorAssociationTime': datetime(2015, 1, 1)
                                },
                            ],
                            'NetworkInterfaces': [
                                {
                                    'Association': {
                                        'CarrierIp': 'string',
                                        'CustomerOwnedIp': 'string',
                                        'IpOwnerId': 'string',
                                        'PublicDnsName': 'string',
                                        'PublicIp': 'string'
                                    },
                                    'Attachment': {
                                        'AttachTime': datetime(2015, 1, 1),
                                        'AttachmentId': 'string',
                                        'DeleteOnTermination': True|False,
                                        'DeviceIndex': 123,
                                        'Status': 'attaching'|'attached'|'detaching'|'detached',
                                        'NetworkCardIndex': 123
                                    },
                                    'Description': 'string',
                                    'Groups': [
                                        {
                                            'GroupName': 'string',
                                            'GroupId': 'string'
                                        },
                                    ],
                                    'Ipv6Addresses': [
                                        {
                                            'Ipv6Address': 'string'
                                        },
                                    ],
                                    'MacAddress': 'string',
                                    'NetworkInterfaceId': 'string',
                                    'OwnerId': 'string',
                                    'PrivateDnsName': 'string',
                                    'PrivateIpAddress': 'string',
                                    'PrivateIpAddresses': [
                                        {
                                            'Association': {
                                                'CarrierIp': 'string',
                                                'CustomerOwnedIp': 'string',
                                                'IpOwnerId': 'string',
                                                'PublicDnsName': 'string',
                                                'PublicIp': 'string'
                                            },
                                            'Primary': True|False,
                                            'PrivateDnsName': 'string',
                                            'PrivateIpAddress': 'string'
                                        },
                                    ],
                                    'SourceDestCheck': True|False,
                                    'Status': 'available'|'associated'|'attaching'|'in-use'|'detaching',
                                    'SubnetId': 'string',
                                    'VpcId': 'string',
                                    'InterfaceType': 'string',
                                    'Ipv4Prefixes': [
                                        {
                                            'Ipv4Prefix': 'string'
                                        },
                                    ],
                                    'Ipv6Prefixes': [
                                        {
                                            'Ipv6Prefix': 'string'
                                        },
                                    ]
                                },
                            ],
                            'OutpostArn': 'string',
                            'RootDeviceName': 'string',
                            'RootDeviceType': 'ebs'|'instance-store',
                            'SecurityGroups': [
                                {
                                    'GroupName': 'string',
                                    'GroupId': 'string'
                                },
                            ],
                            'SourceDestCheck': True|False,
                            'SpotInstanceRequestId': 'string',
                            'SriovNetSupport': 'string',
                            'StateReason': {
                                'Code': 'string',
                                'Message': 'string'
                            },
                            'Tags': [
                                {
                                    'Key': 'string',
                                    'Value': 'string'
                                },
                            ],
                            'VirtualizationType': 'hvm'|'paravirtual',
                            'CpuOptions': {
                                'CoreCount': 123,
                                'ThreadsPerCore': 123
                            },
                            'CapacityReservationId': 'string',
                            'CapacityReservationSpecification': {
                                'CapacityReservationPreference': 'open'|'none',
                                'CapacityReservationTarget': {
                                    'CapacityReservationId': 'string',
                                    'CapacityReservationResourceGroupArn': 'string'
                                }
                            },
                            'HibernationOptions': {
                                'Configured': True|False
                            },
                            'Licenses': [
                                {
                                    'LicenseConfigurationArn': 'string'
                                },
                            ],
                            'MetadataOptions': {
                                'State': 'pending'|'applied',
                                'HttpTokens': 'optional'|'required',
                                'HttpPutResponseHopLimit': 123,
                                'HttpEndpoint': 'disabled'|'enabled',
                                'HttpProtocolIpv6': 'disabled'|'enabled'
                            },
                            'EnclaveOptions': {
                                'Enabled': True|False
                            },
                            'BootMode': 'legacy-bios'|'uefi',
                            'PlatformDetails': 'string',
                            'UsageOperation': 'string',
                            'UsageOperationUpdateTime': datetime(2015, 1, 1),
                            'PrivateDnsNameOptions': {
                                'HostnameType': 'ip-name'|'resource-name',
                                'EnableResourceNameDnsARecord': True|False,
                                'EnableResourceNameDnsAAAARecord': True|False
                            },
                            'Ipv6Address': 'string'
                        },
                    ],
                    'OwnerId': 'string',
                    'RequesterId': 'string',
                    'ReservationId': 'string'
                },
            ],
            'NextToken': 'string'
        }

        :param instance_ids:
        :return:
        """
        client = self._session.client('ec2')
        response = client.describe_instances(
            InstanceIds=instance_ids
        )
        return response
