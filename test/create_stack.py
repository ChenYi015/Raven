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

from benchmark.cloud.provider import Provider

import configs
<<<<<<< HEAD
from benchmark.cloud.provider import Provider
=======
>>>>>>> c6e57f152b6cf3642e1037d16220c2d7462bcd36

if __name__ == '__main__':
    aws = Provider(configs.PROVIDER_CONFIG)

    # VPC
    path = os.path.join(os.environ['RAVEN_HOME'], 'configs', 'providers', 'aws', 'vpc-cloudformation-template.yaml')
    with open(path, encoding='utf-8') as file:
        template = file.read()
    aws.create_stack(
        stack_name='Raven-VPC-Stack',
        template_body=template
    )

    # IAM
    path = os.path.join(os.environ['RAVEN_HOME'], 'configs', 'providers', 'aws', 'iam-cloudformation-template.yaml')
    with open(path, encoding='utf-8') as file:
        template = file.read()
    aws.create_stack(
        stack_name='Raven-IAM-Stack',
        template_body=template
    )

    # MySQL for Hadoop Hive
    # path = os.path.join(os.environ['RAVEN_HOME'], 'configs', 'providers', 'aws', 'mysql',
    #                     'mysql-cloudformation-template.yaml')
    # with open(path, encoding='utf-8') as file:
    #     template = file.read()
    # aws.create_stack(
    #     stack_name='Raven-MySQL-Stack',
    #     template_body=template,
    #     Ec2KeyName='key_raven'
    # )

    # Hadoop ResourceManager
    # path = os.path.join(os.environ['RAVEN_HOME'], 'configs', 'providers', 'aws', 'hadoop-2.10.1',
    #                     'hadoop-2.10.1-resourcemanager-cloudformation-template.yaml')
    # with open(path, encoding='utf-8') as file:
    #     template = file.read()
    # aws.create_stack(
    #     stack_name='Raven-Hadoop-ResourceManager-Stack',
    #     template_body=template,
    #     Ec2KeyName='key_raven'
    # )

    # Hadoop NodeManager
    # path = os.path.join(os.environ['RAVEN_HOME'], 'configs', 'providers', 'aws', 'hadoop-2.10.1',
    #                     'hadoop-2.10.1-nodemanager-cloudformation-template.yaml')
    # with open(path, encoding='utf-8') as file:
    #     template = file.read()
    # aws.create_stack(
    #     stack_name='Raven-Hadoop-NodeManager-Stack',
    #     template_body=template,
    #     Ec2KeyName='key_raven'
    # )

    # Spark Master
    path = os.path.join(os.environ['RAVEN_HOME'], 'configs', 'providers', 'aws', 'spark-3.1.1',
                        'spark-master-cloudformation-template.yaml')
    with open(path, encoding='utf-8') as file:
        template = file.read()
    aws.create_stack(
        stack_name='Raven-Spark-Master-Stack',
        template_body=template,
        Ec2KeyName='key_raven'
    )

    # Spark Worker
    # path = os.path.join(os.environ['RAVEN_HOME'], 'configs', 'providers', 'aws', 'spark-3.1.1',
    #                     'spark-worker-cloudformation-template.yaml')
    # with open(path, encoding='utf-8') as file:
    #     template = file.read()
    # workers = 2
    # for worker_id in range(1, workers + 1):
    #     aws.create_stack(
    #         stack_name=f'Raven-Spark-Worker{worker_id}-Stack',
    #         template_body=template,
    #         Ec2KeyName='key_raven',
    #         SparkWorkerName=f'Spark Worker {worker_id}'
    #     )
