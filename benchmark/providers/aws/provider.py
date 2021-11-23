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
        self._name = 'Amazon Web Service'
        self._region = config['Properties']['Region']
        self._key_name = config['Properties']['KeyName']
        self._session = boto3.session.Session(region_name=self._region)

    @property
    def name(self):
        return self._name

    def exists_stack(self, stack_name: str) -> bool:
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
        try:
            client = self._session.client('cloudformation')
            response = client.create_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Capabilities=['CAPABILITY_NAMED_IAM'],
                Tags=tags if tags else [],
                **kwargs
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
        client = self._session.client('cloudformation')
        client.delete_stack(StackName=stack_name)
        self._wait_stack_delete_complete(stack_name=stack_name)

    def create_emr_stack_for_engine(self, engine: str = 'all', tags=None) -> (str, str):
        """
        Create AWS EMR cluster for engine.
        :param engine: The name of engine, allowed values are hive, spark-sql, presto.
        :param tags: The tags of AWS EMR cluster.
        :return: The stack name and AWS EMR cluster ID.
        """
        logger.info(f'Creating EMR cluster for {engine.capitalize()}...')
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        stack_name = f'EMR-Raven-Stack-for-{engine.capitalize()}-{random_suffix}'
        if engine == 'all':
            filename = 'cloudformation-template.yaml'
        else:
            filename = f'{engine}-cloudformation.yaml'
        with open(os.path.join(os.environ['RAVEN_HOME'], 'configs', 'providers', 'aws', filename), encoding='utf-8') as file:
            template_body = file.read()
        self.create_stack(stack_name=stack_name, template_body=template_body, tags=tags if tags else [])

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
            logger.error(error)

        logger.info(f'AWS has finished creating EMR cluster, cluster id: {cluster_id}.')
        return stack_name, cluster_id

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

            # my_response = []
            # for metric_data_result in response['MetricDataResults']:
            #     metric = {'Label': metric_data_result['Label'], 'Timestamps': [], 'Values': []}
            #     for timestamp in metric_data_result['Timestamps']:
            #         metric['Timestamps'].append(timestamp.timestamp())
            #     for value in metric_data_result['Values']:
            #         metric['Values'].append(value)
            # return my_response

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
