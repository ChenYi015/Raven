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
import threading
from typing import List

from benchmark.cloud.aws.aws import Ec2Instance, AmazonWebService

logger = logging.getLogger()


class HadoopResourceManager(Ec2Instance):

    def __init__(self, *, aws: AmazonWebService = None, region: str = '', ec2_key_name: str = '',
                 ec2_instance_type: str):
        path = os.path.join(os.environ['RAVEN_HOME'], 'config', 'cloud', 'aws', 'hadoop',
                            'hadoop-resourcemanager-cloudformation-template.yaml')
        with open(path, encoding='utf-8') as file:
            template = file.read()

        super().__init__(
            name='HadoopResourceManager',
            aws=aws,
            region=region,
            stack_name='Raven-Hadoop-ResourceManager-Stack',
            template=template,
            ec2_key_name=ec2_key_name,
            ec2_instance_type=ec2_instance_type
        )

    def __str__(self):
        return f'{self.name}(PublicIp={self.public_ip}, PrivateIp={self.private_ip})'

    def launch(self):
        logger.info('Hadoop ResourceManager is launching...')
        super().launch()
        logger.info('Hadoop ResourceManager has launched.')

    def terminate(self):
        logger.info('Hadoop ResourceManager is terminating...')
        super().terminate()
        logger.info('Hadoop ResourceManager has terminated.')


class HadoopNodeManager(Ec2Instance):

    def __init__(self, *, aws: AmazonWebService = None, region: str = '', ec2_key_name: str = '',
                 ec2_instance_type: str, node_manager_id: int = 1):
        path = os.path.join(os.environ['RAVEN_HOME'], 'config', 'cloud', 'aws', 'hadoop',
                            'hadoop-nodemanager-cloudformation-template.yaml')
        with open(path, encoding='utf-8') as file:
            template = file.read()

        super().__init__(
            name=f'HadoopNodeManager{node_manager_id}',
            aws=aws,
            region=region,
            stack_name=f'Raven-Hadoop-Nodemanager{node_manager_id}-Stack',
            template=template,
            ec2_key_name=ec2_key_name,
            ec2_instance_type=ec2_instance_type,
            HadoopNodeManagerId=node_manager_id
        )

        self._node_manager_id = node_manager_id

    @property
    def node_manager_id(self):
        return self._node_manager_id

    def __str__(self):
        return f'{self.name}(PublicIp={self.public_ip}, PrivateIp={self.private_ip})'

    def launch(self):
        logger.info(f'Hadoop NodeManager {self._node_manager_id} is launching...')
        super().launch()
        logger.info(f'Hadoop NodeManager {self._node_manager_id} has launched.')

    def terminate(self):
        logger.info(f'Hadoop NodeManager {self._node_manager_id} is terminating...')
        super().terminate()
        logger.info(f'Hadoop NodeManager {self._node_manager_id} has terminated.')


class HadoopCluster:

    def __init__(self, aws: AmazonWebService, master_instance_type: str = 't2.small', node_manager_num: int = 0,
                 node_manager_instance_type: str = 't2.small'):
        self._resource_manager = HadoopResourceManager(aws=aws, ec2_instance_type=master_instance_type)
        self._node_managers: List[HadoopNodeManager] = [
            HadoopNodeManager(aws=aws, ec2_instance_type=node_manager_instance_type, node_manager_id=node_manager_id)
            for node_manager_id in range(1, node_manager_num + 1)
        ]

    @property
    def resource_manager(self):
        return self._resource_manager

    @property
    def node_managers(self):
        return self._node_managers

    def __str__(self):
        return f'HadoopCluster(ResourceManager={self.resource_manager}, #NodeManager={len(self.node_managers)})'

    def launch(self):
        logger.info('Hadoop cluster is launching...')

        self.resource_manager.launch()

        threads: List[threading.Thread] = []
        for worker in self.node_managers:
            thread = threading.Thread(target=worker.launch)
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()

        logger.info('Hadoop cluster has launched.')

    def terminate(self):
        logger.info('Hadoop cluster is terminating...')

        threads: List[threading.Thread] = []
        for worker in self.node_managers:
            thread = threading.Thread(target=worker.terminate)
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()

        self.resource_manager.terminate()

        logger.info('Hadoop cluster has terminated.')


if __name__ == '__main__':
    import configs
    config = configs.CLOUD_CONFIG['Properties']
    aws = AmazonWebService(
        region=config['Region'],
        ec2_key_name=config['Ec2KeyName']
    )
    hadoop_cluster = HadoopCluster(
        aws=aws,
        master_instance_type=config['MasterInstanceType'],
        node_manager_instance_type=config['CoreInstanceType'],
        node_manager_num=config['CoreInstanceCount']
    )
    hadoop_cluster.launch()
    hadoop_cluster.terminate()
