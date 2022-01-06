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
import time
from datetime import datetime, timezone
from pprint import pprint
from typing import List, Optional

import boto3
import botocore.exceptions
import pandas as pd

import configs
from benchmark.tools import ssh_exec_commands

logger = configs.ROOT_LOGGER


class StackStatus:
    UNDEFINED = 'UNDEFINED'
    CREATE_IN_PROGRESS = 'CREATE_IN_PROGRESS'
    CREATE_COMPLETED = 'CREATE_COMPLETE'
    CREATE_FAILED = 'CREATE_FAILED'
    ROLLBACK_IN_PROGRESS = 'ROLLBACK_IN_PROGRESS'
    ROLLBACK_COMPLETE = 'ROLLBACK_COMPLETE'
    ROLLBACK_FAILED = 'ROLLBACK_FAILED'
    DELETE_IN_PROGRESS = 'DELETE_IN_PROGRESS'
    DELETE_COMPLETE = 'DELETE_COMPLETE'
    DELETE_FAILED = 'DELETE_FAILED'


class AmazonWebService:

    def __init__(self, region: str, ec2_key_name: str = ''):
        self.name = 'Amazon Web Service'
        self._region = region
        self._session = boto3.session.Session(region_name=self._region)
        self._ec2_key_name = ec2_key_name

    @property
    def region(self):
        return self._region

    @region.setter
    def region(self, value):
        self.region = value

    @property
    def session(self):
        return self._session

    @property
    def ec2_key_name(self):
        return self._ec2_key_name

    @ec2_key_name.setter
    def ec2_key_name(self, value):
        self._ec2_key_name = value

    # S3
    def create_bucket(self, bucket_name: str, region_name: str = None):
        """Create an S3 bucket in a specified region.

        If a region is not specified, the bucket is created in the S3 default
        region (us-east-1).

        :param bucket_name: Bucket to create
        :param region_name: Region to create bucket in, e.g. 'us-west-2'
        :return: True if bucket created, else False
        """

        try:
            if not region_name:
                client = self._session.client('s3')
                client.create_bucket(Bucket=bucket_name)
            else:
                client = self._session.client('s3', region_name=region_name)
                client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={
                        'LocationConstraint': region_name
                    }
                )
        except botocore.exceptions.ClientError as error:
            logger.error(error.response['Error']['Message'])
            return False
        return True

    def list_buckets(self):
        """List all the existing buckets for the AWS account.

        :return:
        """
        client = self._session.client('s3')
        response = client.list_buckets()
        return [bucket for bucket in response['Buckets']]

    def upload_file(self, file_name, bucket_name, object_name=None) -> bool:
        """Upload a file to an S3 bucket.

        :param file_name: File to upload
        :param bucket_name: Bucket to upload to
        :param object_name: S3 object name. If not specified then file_name is
        :return: True if file was uploaded, else False
        """

        # If S3 object_name was not specified, use file_name
        if object_name is None:
            object_name = os.path.basename(file_name)

        # Upload the file
        s3_client = self._session.client('s3')
        try:
            s3_client.upload_file(file_name, bucket_name, object_name)
        except botocore.exceptions.ClientError as error:
            logger.error(error['Response']['Message'])
            return False
        return True

    def download_file(self, bucket_name, object_name, file_name) -> bool:
        s3_client = self._session.client('s3')
        try:
            s3_client.download_file(bucket_name, object_name, file_name)
        except botocore.exceptions.ClientError as error:
            logger.error(error['Response']['Message'])
            return False
        return True

    # EC2
    def describe_ec2_instances(self, instance_ids: list) -> dict:
        """Describe AWS EC2 instance.

        Detailed documentation: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_instances
        :param instance_ids:
        :return:
        """
        client = self._session.client('ec2')
        response = client.describe_instances(
            InstanceIds=instance_ids
        )
        return response

    def create_ec2_stack_for_athena(self, tags=None) -> (str, str):
        """
        Create AWS EC2 instance for engine.
        :param tags: The tags of AWS EMR cluster.
        :return: AWS EC2 ID and public ip.
        """
        logger.info(f'AWS is creating EC2 instance for Athena...')
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        stack_name = f'Raven-Stack-for-Athena-{random_suffix}'
        with open(os.path.join(os.environ['RAVEN_HOME'], 'config', 'cloud', 'aws', 'athena-cloudformation.yaml'),
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

    def monitor_kylin4_ec2_cluster(self, master_instance_id: str, start: datetime, end: datetime):
        """
        Monitor AWS EMR cluster and write metrics into files.
        :param master_instance_id: The instance id of Kylin4 resource_manager node.
        :param start: The run timestamp.
        :param end: The end timestamp.
        :return:
        """
        logger.info(f'AWS is monitoring Kylin4 EC2 cluster, resource_manager instance id: {master_instance_id}...')
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

    # EMR
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

    def setup_emr_master_with_commands(self, ec2_key_name: str, cluster_id: str, commands: List[str]):
        """
        Setup AWS EMR
        :param ec2_key_name:
        :param commands: Commands for setting up EMR cluster nodes.
        :param cluster_id: The ID of AWS EMR Cluster.
        :return:
        """
        logger.info(f'AWS is setting up EMR cluster resource_manager nodes, cluster id: {cluster_id}...')
        if commands is None:
            commands = []
        master_ips = self.get_emr_master_public_ips(cluster_id=cluster_id)
        for hostname in master_ips:
            ssh_exec_commands(
                hostname=hostname,
                commands=commands,
                key_name=ec2_key_name
            )
        logger.info(f'AWS has finished setting up EMR cluster resource_manager nodes.')

    def setup_emr_core_with_commands(self, ec2_key_name: str, cluster_id: str, commands: List[str]):
        """
        Setup AWS EMR
        :param ec2_key_name:
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
                key_name=ec2_key_name
            )
        logger.info(f'AWS has finished setting up EMR cluster core nodes.')

    def setup_emr_with_commands(self, ec2_key_name: str, cluster_id: str, commands: List[str]):
        """
        Setup AWS EMR
        :param ec2_key_name:
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
                key_name=ec2_key_name
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

    def create_emr_stack_for_engine(self, engine: str = 'all', tags=None, *, install_cwa: bool = False) -> (str, str):
        """
        Create AWS EMR cluster for engine.
        :param install_cwa:
        :param engine: The name of engine, allowed values are hive, spark-sql, presto.
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
        with open(os.path.join(os.environ['RAVEN_HOME'], 'config', 'cloud', 'aws', 'emr', filename),
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

    # CloudFormation
    def get_stack_status(self, stack_name: str) -> str:
        try:
            response = self._session.client('cloudformation').describe_stacks(StackName=stack_name)
            return response['Stacks'][0]['StackStatus']
        except botocore.exceptions.ClientError:
            return StackStatus.UNDEFINED

    def exists_stack(self, stack_name: str) -> bool:
        """
        Test whether stack with specified name exists.
        :param stack_name: Name of stack.
        :return:
        """

        if self.get_stack_status(stack_name) != StackStatus.UNDEFINED:
            return True
        else:
            return False

    def create_stack(self, stack_name: str, template_body: str, tags=None, **kwargs):
        """
                Create stack by AWS CloudFormation template.
                :param stack_name: The name of the stack.
                :param template_body: Cloudformation template.
                :param tags: The tags of stack.
                :param wait: Wait stack create complete.
                :return:
                """
        # Create CloudFormation client
        if self.exists_stack(stack_name=stack_name):
            logger.debug(f'Stack [{stack_name}] already exists.')
            return

        # Create stack
        logger.debug(f'Creating stack [{stack_name}]...')
        parameters = []
        for key, value in kwargs.items():
            parameters.append(
                {
                    'ParameterKey': key,
                    'ParameterValue': str(value)
                }
            )
        try:
            client = self._session.client('cloudformation')
            client.create_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Capabilities=['CAPABILITY_NAMED_IAM'],
                Tags=tags if tags else [],
                Parameters=parameters
            )
            logger.debug(f'Waiting for stack [{stack_name}] creation to complete...')
            self.wait_stack_create_complete(stack_name=stack_name)
            logger.debug(f'Stack [{stack_name}] has been created.')
        except botocore.exceptions.ClientError as error:
            logger.error(error.response['Error']['Message'])

    def delete_stack(self, stack_name: str):
        if not self.exists_stack(stack_name=stack_name):
            return
        logger.debug(f'Deleting stack [{stack_name}]...')
        client = self._session.client('cloudformation')
        try:
            client.delete_stack(StackName=stack_name)
        except botocore.exceptions.ClientError as error:
            logger.error(error.response['Error']['Message'])
        self.wait_stack_delete_complete(stack_name=stack_name)
        logger.debug(f'AWS has finished deleting Stack [{stack_name}].')

    def describe_stack(self, stack_name: str) -> Optional[dict]:
        client = self._session.client('cloudformation')
        try:
            response = client.describe_stacks(
                StackName=stack_name
            )
            return response
        except botocore.exceptions.ValidationError as error:
            logger.error(error.with_traceback())

    def wait_stack_create_complete(self, stack_name: str) -> bool:
        client = self._session.client('cloudformation')
        waiter = client.get_waiter('stack_create_complete')
        try:
            waiter.wait(StackName=stack_name)
            return True
        except botocore.exceptions.WaiterError as error:
            logger.error(error.last_response['Error']['Message'])
            return False

    def wait_stack_delete_complete(self, stack_name: str) -> bool:
        client = self._session.client('cloudformation')
        waiter = client.get_waiter('stack_delete_complete')
        try:
            waiter.wait(StackName=stack_name)
            return True
        except botocore.exceptions.WaiterError as error:
            logger.error(error.last_response['Error']['Message'])
            return False

    def wait_stack_import_complete(self, stack_name: str) -> bool:
        """

        :param stack_name:
        :return:
        """
        client = self._session.client('cloudformation')
        waiter = client.get_waiter('stack_import_complete')
        try:
            waiter.wait(StackName=stack_name)
            return True
        except botocore.exceptions.WaiterError as error:
            logger.error(error.last_response['Error']['Message'])
            return False

    def wait_stack_exists(self, stack_name: str) -> bool:
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

    def wait_stack_rollback_complete(self, stack_name: str) -> bool:
        client = self._session.client('cloudformation')
        waiter = client.get_waiter('stack_rollback_complete')
        try:
            waiter.wait(StackName=stack_name)
            return True
        except botocore.exceptions.WaiterError as error:
            logger.error(error.last_response['Error']['Message'])
            return False

    def wait_stack_update_complete(self, stack_name: str) -> bool:
        client = self._session.client('cloudformation')
        waiter = client.get_waiter('stack_update_complete')
        try:
            waiter.wait(StackName=stack_name)
            return True
        except botocore.exceptions.WaiterError as error:
            logger.error(error.last_response['Error']['Message'])
        return False

    def get_stack_output_by_key(self, stack_name, output_key: str) -> Optional[str]:
        response = self.describe_stack(stack_name=stack_name)
        outputs = response['Stacks'][0]['Outputs']
        for output in outputs:
            if output['OutputKey'] == output_key:
                return output['OutputValue']

    # CloudWatch
    def list_metrics(self, dimensions: List[dict], metric_name: str, namespace: str):
        """

        :param dimensions:
        :param metric_name:
        :param namespace:
        :return:
        """

        # Create CloudWatch client
        client = self._session.client('cloudwatch')

        # List metrics through the pagination interface
        try:
            paginator = client.get_paginator('list_metrics')
            for response in paginator.paginate(
                    Namespace=namespace,
                    MetricName=metric_name,
                    Dimensions=dimensions
            ):
                print(response['Metrics'])
        except botocore.exceptions.ClientError as error:
            logger.error(error)

    def publish_metrics(self, metric_data: List[dict], namespace):
        """

        :param metric_data:
        :param namespace:
        :return:
        """

        # Create CloudWatch client
        cloudwatch = self._session.client('cloudwatch')

        # Put custom metrics
        # FIXME
        cloudwatch.put_metric_data(
            MetricData=[
                {
                    'MetricName': 'PAGES_VISITED',
                    'Dimensions': [
                        {
                            'Name': 'UNIQUE_PAGES',
                            'Value': 'URLS'
                        },
                    ],
                    'Unit': 'None',
                    'Value': 1.0
                },
            ],
            Namespace='SITE/TRAFFIC'
        )

    def get_metric_data(self, metric_data_queries: List[dict], start_time: datetime,
                        end_time: datetime) -> pd.DataFrame:
        client = self._session.client('cloudwatch')
        paginator = client.get_paginator('get_metric_data')
        metric = pd.DataFrame()
        try:
            response_iterator = paginator.paginate(
                MetricDataQueries=metric_data_queries,
                StartTime=start_time,
                EndTime=end_time,
                ScanBy='TimestampAscending'
            )
            for response in response_iterator:
                data = {
                    metric_data_result['Label']: pd.Series(
                        data=metric_data_result['Values'],
                        index=pd.DatetimeIndex(metric_data_result['Timestamps'], tz=timezone.utc)
                    )
                    for metric_data_result in response['MetricDataResults']
                }
                metric = metric.append(pd.DataFrame(data))
            return metric
        except botocore.exceptions.ClientError as error:
            logger.error(error.response)

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

        with open(os.path.join(os.environ['RAVEN_HOME'], 'config', 'cloud', 'aws',
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

        with open(os.path.join(os.environ['RAVEN_HOME'], 'config', 'cloud', 'aws',
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

    # Cost Explorer
    # FIXME
    def get_cost_and_usage(self) -> Optional[dict]:
        """Retrieves cost and usage metrics for your account.

        Detailed reference: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ce.html#CostExplorer.Client.get_cost_and_usage.

        :return:
        """

        client = self._session.client('ce')

        try:
            response = client.get_cost_and_usage(
                TimePeriod={
                    'Start': 'string',
                    'End': 'string'
                },
                Granularity='DAILY' | 'MONTHLY' | 'HOURLY',
                Filter={
                    'Or': [
                        {'... recursive ...'},
                    ],
                    'And': [
                        {'... recursive ...'},
                    ],
                    'Not': {'... recursive ...'},
                    'Dimensions': {
                        'Key': 'AZ' | 'INSTANCE_TYPE' | 'LINKED_ACCOUNT' | 'LINKED_ACCOUNT_NAME' | 'OPERATION' | 'PURCHASE_TYPE' | 'REGION' | 'SERVICE' | 'SERVICE_CODE' | 'USAGE_TYPE' | 'USAGE_TYPE_GROUP' | 'RECORD_TYPE' | 'OPERATING_SYSTEM' | 'TENANCY' | 'SCOPE' | 'PLATFORM' | 'SUBSCRIPTION_ID' | 'LEGAL_ENTITY_NAME' | 'DEPLOYMENT_OPTION' | 'DATABASE_ENGINE' | 'CACHE_ENGINE' | 'INSTANCE_TYPE_FAMILY' | 'BILLING_ENTITY' | 'RESERVATION_ID' | 'RESOURCE_ID' | 'RIGHTSIZING_TYPE' | 'SAVINGS_PLANS_TYPE' | 'SAVINGS_PLAN_ARN' | 'PAYMENT_OPTION' | 'AGREEMENT_END_DATE_TIME_AFTER' | 'AGREEMENT_END_DATE_TIME_BEFORE',
                        'Values': [
                            'string',
                        ],
                        'MatchOptions': [
                            'EQUALS' | 'ABSENT' | 'STARTS_WITH' | 'ENDS_WITH' | 'CONTAINS' | 'CASE_SENSITIVE' | 'CASE_INSENSITIVE',
                        ]
                    },
                    'Tags': {
                        'Key': 'string',
                        'Values': [
                            'string',
                        ],
                        'MatchOptions': [
                            'EQUALS' | 'ABSENT' | 'STARTS_WITH' | 'ENDS_WITH' | 'CONTAINS' | 'CASE_SENSITIVE' | 'CASE_INSENSITIVE',
                        ]
                    },
                    'CostCategories': {
                        'Key': 'string',
                        'Values': [
                            'string',
                        ],
                        'MatchOptions': [
                            'EQUALS' | 'ABSENT' | 'STARTS_WITH' | 'ENDS_WITH' | 'CONTAINS' | 'CASE_SENSITIVE' | 'CASE_INSENSITIVE',
                        ]
                    }
                },
                Metrics=[
                    'string',
                ],
                GroupBy=[
                    {
                        'Type': 'DIMENSION' | 'TAG' | 'COST_CATEGORY',
                        'Key': 'string'
                    },
                ],
                NextPageToken='string'
            )
            return response
        except botocore.exceptions.ClientError as error:
            logger.error(error['Response']['Message'])

    # Raven
    def create_vpc_stack(self):
        path = os.path.join(os.environ['RAVEN_HOME'], 'config', 'cloud', 'aws', 'vpc-cloudformation-template.yaml')
        with open(path, encoding='utf-8') as file:
            template = file.read()
        self.create_stack(
            stack_name='Raven-VPC-Stack',
            template_body=template
        )

    def create_iam_stack(self):
        path = os.path.join(os.environ['RAVEN_HOME'], 'config', 'cloud', 'aws', 'iam-cloudformation-template.yaml')
        with open(path, encoding='utf-8') as file:
            template = file.read()
        self.create_stack(
            stack_name='Raven-IAM-Stack',
            template_body=template
        )

    def create_hive_metastore(self, *, ec2_key_name: str):
        self.create_vpc_stack()
        self.create_iam_stack()

        # Hive Metastore(MariaDB)
        path = os.path.join(os.environ['RAVEN_HOME'], 'config', 'cloud', 'aws', 'hive',
                            'hive-metastore-cloudformation-template.yaml')
        with open(path, encoding='utf-8') as file:
            template = file.read()
        self.create_stack(
            stack_name='Raven-Hive-Metastore-Stack',
            template_body=template,
            Ec2KeyName=ec2_key_name
        )

    def terminate_hive_metastore(self):
        self.delete_stack('Raven-Hive-Metastore-Stack')


class Ec2Instance:

    def __init__(self, *, name: str = '', aws: AmazonWebService = None, region: str = '', stack_name: str,
                 template: str, ec2_key_name: str = '', ec2_instance_type: str, tags: dict = None, **kwargs):
        self._name = name

        if aws:
            self._aws = aws
        else:
            self._aws = AmazonWebService(region=region, ec2_key_name=ec2_key_name)
        self._region = self._aws.region
        self._stack_name = stack_name
        self._template = template
        self._ec2_key_name = self._aws.ec2_key_name
        self._ec2_instance_type = ec2_instance_type
        self._tags = tags
        self._kwargs = kwargs

        self._ec2_instance_id = ''
        self._public_ip = ''
        self._private_ip = ''

        self._start: Optional[float] = None
        self._end: Optional[float] = None

    @property
    def name(self):
        return self._name

    @property
    def aws(self):
        return self._aws

    @property
    def region(self) -> str:
        return self.region

    @property
    def stack_name(self) -> str:
        return self._stack_name

    @property
    def tags(self) -> {}:
        return self._tags

    @property
    def kwargs(self):
        return self._kwargs

    @property
    def ec2_key_name(self) -> str:
        return self._ec2_key_name

    @property
    def ec2_instance_type(self) -> str:
        return self._ec2_instance_type

    @property
    def ec2_instance_id(self) -> str:
        if not self._ec2_instance_id:
            self._ec2_instance_id = self.aws.get_stack_output_by_key(stack_name=self.stack_name,
                                                                     output_key='Ec2InstanceId')
        return self._ec2_instance_id

    @property
    def public_ip(self) -> str:
        return self._public_ip

    @property
    def private_ip(self) -> str:
        return self._private_ip

    def __str__(self):
        words = [
            f'Name={self._name}' if self._name else '',
            f'Region={self._region}' if self._region else '',
            f'Ec2KeyName={self._ec2_key_name}' if self._ec2_key_name else '',
            f'StackName={self._stack_name}' if self._stack_name else '',
            f'Tags={self._tags}' if self._tags else '',
            f'PublicIp={self._public_ip}' if self._public_ip else '',
            f'PrivateIp={self._private_ip}' if self._private_ip else ''
        ]
        words = list(filter(lambda word: len(word) != 0, words))
        return 'Ec2Instance(' + ', '.join(words) + ')'

    def launch(self):
        logger.debug(f'{self} is launching...')
        self._aws.create_vpc_stack()
        self._aws.create_iam_stack()
        self._aws.create_stack(
            stack_name=self._stack_name,
            template_body=self._template,
            tags=self._tags,
            Ec2KeyName=self._ec2_key_name,
            Ec2InstanceType=self._ec2_instance_type,
            **self._kwargs
        )
        self._public_ip = self._aws.get_stack_output_by_key(
            stack_name=self._stack_name,
            output_key='Ec2InstancePublicIp'
        )

        self._private_ip = self._aws.get_stack_output_by_key(
            stack_name=self._stack_name,
            output_key='Ec2InstancePrivateIp'
        )
        self._start = time.time()
        logger.debug(f'{self} has launched.')

    def terminate(self):
        logger.debug(f'{self} is terminating...')
        self._aws.delete_stack(stack_name=self._stack_name)
        self._end = time.time()
        logger.debug(f'{self} has terminated.')

    def ssh_exec_commands(self, commands: List[str]):
        ssh_exec_commands(hostname=self.public_ip, port=22, username='ec2-user', key_name=self.ec2_key_name,
                          commands=commands, redirect_output=True)

    def install_cloudwatch_agent(self):
        # FIXME: Configuration file is hard coded
        logger.debug(f'{self} is installing cloudwatch agent...')
        commands = [
            'sudo yum install -y amazon-cloudwatch-agent',
            'sudo mkdir -p /usr/share/collectd',
            'sudo touch /usr/share/collectd/types.db',
            'aws s3 cp s3://chenyi-ap-southeast-1/config/amazon-cloudwatch-agent.json /home/ec2-user',
            'sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s '
            '-c file:/home/ec2-user/amazon-cloudwatch-agent.json'
        ]
        self.ssh_exec_commands(commands=commands)
        logger.debug(f'{self} has finished installing cloudwatch agent...')

    def get_metrics(self, start_time: datetime = None, end_time: datetime = None) -> pd.DataFrame:
        """Get metrics from cloudwatch agent.

        :param start_time:
        :param end_time:
        :return The metrics of the instance in [start_time, end_time]
        """
        logger.debug(f'{self} is pulling metrics from cloudwatch agent...')
        filename = f'cloudwatch-metric-data-queries-for-{self.ec2_instance_type.replace(".", "-")}.json'
        with open(os.path.join(os.environ['RAVEN_HOME'], 'config', 'cloud', 'aws', 'cloudwatch', filename),
                  encoding='utf-8') as file:
            metric_data_queries = json.load(file)
        for metric_data_query in metric_data_queries:
            metric_data_query['MetricStat']['Metric']['Dimensions'].append({
                'Name': 'InstanceId',
                'Value': self.ec2_instance_id
            })
        if not start_time:
            start_time = datetime.fromtimestamp(self._start, tz=timezone.utc)
        if not end_time:
            end_time = datetime.now(tz=timezone.utc)
        metric = self.aws.get_metric_data(
            metric_data_queries=metric_data_queries,
            start_time=start_time,
            end_time=end_time
        )
        logger.debug(f'{self} has finished pulling metrics from cloudwatch agent.')
        return metric

    def get_cost_and_usage(self, start_time: datetime = None, end_time: datetime = None) -> dict:
        client = self.aws.session.client('ce')
        fmt = '%Y-%m-%D %H:%M:%S'
        if not start_time:
            start_time = datetime.fromtimestamp(self._start, tz=timezone.utc).strftime(fmt)
        if not end_time:
            end_time = datetime.now(tz=timezone.utc).strftime(fmt)
        try:
            response = client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_time,
                    'End': end_time
                },
                Granularity='HOURLY',
                Filter={
                    'Dimensions': {
                        'Key': 'RESOURCE_ID',
                        'Values': [self.ec2_instance_id],
                        'MatchOptions': 'EQUALS'
                    }
                },
                Metrics=[
                    'UnblendedCost'
                ]
            )
            return response
        except botocore.exceptions.ClientError as error:
            logger.error(error)
