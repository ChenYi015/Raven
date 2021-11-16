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

import logging
import os
import string
import random
from typing import List

import boto3
import botocore.exceptions

import benchmark.config
from benchmark.tools import ssh_exec_commands


class Provider:

    def __init__(self, config: dict):
        self._name = 'Amazon Web Service'
        self._region = config['Properties']['Region']
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

    def create_emr_for_engine(self, engine: str) -> str:
        """
        Create AWS EMR cluster for engine.
        :param engine: The name of engine, allowed values are hive, spark-sql, presto.
        :return: The ID of AWS EMR cluster.
        """
        logging.info(f'Creating EMR cluster for {engine.capitalize()}...')
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        stack_name = f'EMR-Raven-Stack-for-{engine.capitalize()}-{random_suffix}'
        filename = f'emr-cloudformation-for-{engine}.yaml'
        self.create_stack(stack_name=stack_name, filename=filename, tags=benchmark.config.TAGS)

        client = self._session.client('cloudformation')
        logical_resource_id = 'EMRCluster'
        response = client.describe_stack_resource(StackName=stack_name, LogicalResourceId=logical_resource_id)
        cluster_id = response['StackResourceDetail']['PhysicalResourceId']
        logging.info(f'AWS has finished creating EMR cluster, cluster id: {cluster_id}.')
        return cluster_id

    def describe_emr(self, cluster_id: str):
        # TODO
        pass

    def delete_emr(self, cluster_id: str):
        # TODO
        pass

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
            ssh_exec_commands(
                hostname=hostname,
                commands=commands,
                key_name=benchmark.config.PROVIDER_CONFIG['Properties']['KeyName']
            )
        logging.info(f'AWS has finished setting up EMR cluster.')

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


    # AWS Cost Explorer
    def get_cost_and_usage(self, ):
        # TODO
        pass
