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


class KylinMode:
    ALL = 'all'
    JOB = 'job'
    QUERY = 'query'


class KylinMaster(Ec2Instance):

    def __init__(self, *, aws: AmazonWebService = None, region: str = '', ec2_key_name: str = '',
                 ec2_instance_type: str):
        path = os.path.join(os.environ['RAVEN_HOME'], 'config', 'cloud', 'aws', 'kylin',
                            'kylin-master-cloudformation-template.yaml')
        with open(path, encoding='utf-8') as file:
            template = file.read()

        super().__init__(
            name='KylinMaster',
            aws=aws,
            region=region,
            stack_name='Raven-Kylin-Master-Stack',
            template=template,
            ec2_key_name=ec2_key_name,
            ec2_instance_type=ec2_instance_type
        )

    @property
    def spark_master_url(self):
        return self.aws.get_stack_output_by_key(stack_name=self.stack_name, output_key='SparkMasterUrl')

    def __str__(self):
        return f'{self.name}(PublicIp={self.public_ip}, PrivateIp={self.private_ip})'

    def launch(self):
        logger.info('Kylin master is launching...')
        super().launch()
        logger.info('Kylin master has launched.')

    def terminate(self):
        logger.info('Kylin master is terminating...')
        super().terminate()
        logger.info('Kylin master has terminated.')


class KylinWorker(Ec2Instance):

    def __init__(self, *, aws: AmazonWebService = None, region: str = '', ec2_key_name: str = '',
                 ec2_instance_type: str, worker_id: int = 1):
        path = os.path.join(os.environ['RAVEN_HOME'], 'config', 'cloud', 'aws', 'kylin',
                            'kylin-worker-cloudformation-template.yaml')
        with open(path, encoding='utf-8') as file:
            template = file.read()

        super().__init__(
            name='KylinMaster',
            aws=aws,
            region=region,
            stack_name=f'Raven-Kylin-Worker{worker_id}-Stack',
            template=template,
            ec2_key_name=ec2_key_name,
            ec2_instance_type=ec2_instance_type,
            KylinWorkerId=worker_id,
        )

        self._worker_id = worker_id
        self._spark_master_private_ip = ''

    @property
    def worker_id(self):
        return self._worker_id

    @property
    def spark_master_private_ip(self):
        return self._spark_master_private_ip

    @spark_master_private_ip.setter
    def spark_master_private_ip(self, private_ip: str):
        self._spark_master_private_ip = private_ip
        self.kwargs['SparkMasterPrivateIp'] = private_ip

    def __str__(self):
        return f'{self.name}(PublicIp={self.public_ip}, PrivateIp={self.private_ip})'

    def launch(self):
        logger.info(f'Kylin worker {self._worker_id} is launching...')
        super().launch()
        logger.info(f'Kylin worker {self._worker_id} has launched.')

    def terminate(self):
        logger.info(f'Kylin worker {self._worker_id} is terminating...')
        super().terminate()
        logger.info(f'Kylin worker {self._worker_id} has terminated.')


class KylinCluster:

    def __init__(self, *, aws: AmazonWebService, master_instance_type: str = 't2.small', worker_num: int = 0,
                 worker_instance_type: str = 't2.small'):
        self._aws = aws
        self._master_instance_type = master_instance_type
        self._worker_instance_type = worker_instance_type
        self._master = KylinMaster(aws=aws, ec2_instance_type=self._master_instance_type)
        self._workers: List[KylinWorker] = [
            KylinWorker(aws=aws, ec2_instance_type=self._worker_instance_type, worker_id=worker_id) for worker_id in
            range(0, worker_num)]

    @property
    def master(self):
        return self._master

    @property
    def workers(self):
        return self._workers

    def __str__(self):
        return f'KylinCluster(Master={self.master}, #Worker={len(self.workers)})'

    def launch(self):
        logger.info('Kylin cluster is launching...')

        self.master.launch()

        threads: List[threading.Thread] = []
        for worker in self.workers:
            worker.spark_master_private_ip = self.master.private_ip
            thread = threading.Thread(target=worker.launch)
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()

        logger.info('Kylin cluster has launched.')

    def terminate(self):
        logger.info('Kylin cluster is terminating...')

        threads: List[threading.Thread] = []
        for worker in self.workers:
            thread = threading.Thread(target=worker.terminate)
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()

        self.master.terminate()

        logger.info('Kylin cluster has terminated.')

    def scale(self, worker_num: int):
        logger.info('Kylin cluster is scaling...')
        n = len(self.workers)
        threads: List[threading.Thread] = []
        if worker_num < n:
            for worker_id in range(worker_num, n):
                thread = threading.Thread(target=self.workers[worker_id].terminate)
                thread.start()
                threads.append(thread)
        elif worker_num > n:
            for worker_id in range(n, worker_num):
                worker = KylinWorker(aws=self._aws, ec2_instance_type=self._worker_instance_type, worker_id=worker_id)
                worker.spark_master_private_ip = self.master.private_ip
                self.workers.append(worker)
                thread = threading.Thread(target=worker.launch)
                thread.start()
                threads.append(thread)
        for thread in threads:
            thread.join()
        logger.info('Kylin cluster has finished scaling.')
