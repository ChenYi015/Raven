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

import os

import configs
from benchmark.providers.aws.provider import Provider

if __name__ == '__main__':
    aws = Provider(configs.PROVIDER_CONFIG)

    # VPC
    path = os.path.join(os.environ['RAVEN_HOME'], 'configs', 'providers', 'aws', 'vpc-cloudformation-template.yaml')
    with open(path, encoding='utf-8') as file:
        template = file.read()
    aws.create_stack(
        stack_name='RAVEN-VPC-STACK',
        template_body=template
    )

    # IAM
    path = os.path.join(os.environ['RAVEN_HOME'], 'configs', 'providers', 'aws', 'iam-cloudformation-template.yaml')
    with open(path, encoding='utf-8') as file:
        template = file.read()
    aws.create_stack(
        stack_name='RAVEN-IAM-STACK',
        template_body=template
    )

    # MySQL
    path = os.path.join(os.environ['RAVEN_HOME'], 'configs', 'providers', 'aws', 'mysql-cloudformation-template.yaml')
    with open(path, encoding='utf-8') as file:
        template = file.read()
    aws.create_stack(
        stack_name='RAVEN-MySQL-STACK',
        template_body=template,
        Ec2KeyName='key_raven'
    )

    # Hadoop ResourceManager
    path = os.path.join(os.environ['RAVEN_HOME'], 'configs', 'providers', 'aws',
                        'hadoop-resourcemanager-cloudformation-template.yaml')
    with open(path, encoding='utf-8') as file:
        template = file.read()
    aws.create_stack(
        stack_name='RAVEN-Hadoop-ResourceManager-STACK',
        template_body=template,
        Ec2KeyName='key_raven'
    )

    # Hadoop NodeManager
    path = os.path.join(os.environ['RAVEN_HOME'], 'configs', 'providers', 'aws',
                        'hadoop-nodemanager-cloudformation-template.yaml')
    with open(path, encoding='utf-8') as file:
        template = file.read()
    aws.create_stack(
        stack_name='RAVEN-Hadoop-NodeManager-STACK',
        template_body=template,
        Ec2KeyName='key_raven'
    )