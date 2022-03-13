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
import threading
import time
from typing import List

from benchmark.cloud.aws.aws import Ec2Instance, AmazonWebService
from benchmark.tools import get_random_id

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
            name='KylinWorker',
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
        self._cluster_id = get_random_id(16)

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

    def install_cloud_watch_agent(self):
        logger.debug('Kylin cluster is installing cloudwatch agent...')
        threads: List[threading.Thread] = [threading.Thread(target=self.master.install_cloudwatch_agent)]
        for worker in self.workers:
            threads.append(threading.Thread(target=worker.install_cloudwatch_agent))
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        logger.debug('Kylin cluster has finished installing cloudwatch agent.')

    def collect_cluster_info(self, output_dir: str = None):
        """Collect kylin cluster information.
        :param output_dir:
        :return:
        """
        if not output_dir:
            output_dir = os.path.join(os.environ['RAVEN_HOME'], 'out', 'cluster', f'kylin-{self._cluster_id}')
        os.makedirs(output_dir, exist_ok=True)
        info = {
            'Master': self.master.to_dict(),
            'Workers': [worker.to_dict() for worker in self.workers]
        }
        with open(os.path.join(output_dir, f'cluster-info_{time.strftime("%Y-%m-%d_%H-%M-%S")}.json'), mode='w',
                  encoding='utf-8') as file:
            json.dump(info, file, indent=2)

    def collect_metrics(self, output_dir: str = None):
        logger.debug('Kylin cluster is pulling metrics cloudwatch agent...')
        if not output_dir:
            output_dir = os.path.join(os.environ['RAVEN_HOME'], 'out', 'cluster', f'kylin-{self._cluster_id}')
        os.makedirs(output_dir, exist_ok=True)
        threads: List[threading.Thread] = [
            threading.Thread(target=self.master.collect_metrics, kwargs={'output_dir': output_dir})]
        for worker in self.workers:
            threads.append(threading.Thread(target=worker.collect_metrics, kwargs={'output_dir': output_dir}))
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        logger.debug('Kylin cluster has finished pulling metrics cloudwatch agent...')

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
