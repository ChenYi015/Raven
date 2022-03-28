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
import logging
import threading
import time
from typing import List

from benchmark.cloud.aws.aws import Ec2Instance, AmazonWebService
from benchmark.tools import get_random_id

logger = logging.getLogger()


class SparkMaster(Ec2Instance):

    def __init__(self, *, aws: AmazonWebService = None, region: str = '', ec2_key_name: str = '',
                 ec2_instance_type: str):
        path = os.path.join(os.environ['RAVEN_HOME'], 'config', 'cloud', 'aws', 'spark',
                            'spark-master-cloudformation-template.yaml')
        with open(path, encoding='utf-8') as file:
            template = file.read()

        super().__init__(
            name='SparkMaster',
            aws=aws,
            region=region,
            stack_name='Raven-Spark-Master-Stack',
            template=template,
            ec2_key_name=ec2_key_name,
            ec2_instance_type=ec2_instance_type
        )

    def __str__(self):
        return f'{self.name}(PublicIp={self.public_ip}, PrivateIp={self.private_ip})'

    def launch(self):
        logger.info('Spark master is launching...')
        super().launch()
        logger.info('Spark master has launched.')

    def terminate(self):
        logger.info('Spark master is terminating...')
        super().terminate()
        logger.info('Spark master has terminated.')


class SparkWorker(Ec2Instance):

    def __init__(self, *, aws: AmazonWebService = None, region: str = '', ec2_key_name: str = '',
                 ec2_instance_type: str, worker_id: int = 1):
        path = os.path.join(os.environ['RAVEN_HOME'], 'config', 'cloud', 'aws', 'spark',
                            'spark-worker-cloudformation-template.yaml')
        with open(path, encoding='utf-8') as file:
            template = file.read()

        super().__init__(
            name=f'SparkWorker{worker_id}',
            aws=aws,
            region=region,
            stack_name=f'Raven-Spark-Worker{worker_id}-Stack',
            template=template,
            ec2_key_name=ec2_key_name,
            ec2_instance_type=ec2_instance_type,
            SparkWorkerId=worker_id
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
        logger.info(f'Spark worker {self._worker_id} is launching...')
        super().launch()
        logger.info(f'Spark worker {self._worker_id} has launched.')

    def terminate(self):
        logger.info(f'Spark worker {self._worker_id} is terminating...')
        super().terminate()
        logger.info(f'Spark worker {self._worker_id} has terminated.')


class SparkCluster:

    def __init__(self, aws: AmazonWebService, master_instance_type: str = 't2.small', worker_num: int = 0,
                 worker_instance_type: str = 't2.small'):
        self._master = SparkMaster(aws=aws, ec2_instance_type=master_instance_type)
        self._workers: List[SparkWorker] = [
            SparkWorker(aws=aws, ec2_instance_type=worker_instance_type, worker_id=worker_id) for worker_id in
            range(1, worker_num + 1)]
        self._cluster_id = get_random_id(16)

    @property
    def master(self):
        return self._master

    @property
    def workers(self):
        return self._workers

    def __str__(self):
        return f'SparkCluster(Master={self.master}, #Worker={len(self.workers)})'

    def launch(self):
        logger.info('Spark cluster is launching...')

        self.master.launch()

        threads: List[threading.Thread] = []
        for worker in self.workers:
            worker.spark_master_private_ip = self.master.private_ip
            thread = threading.Thread(target=worker.launch)
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()

        logger.info('Spark cluster has launched.')

    def terminate(self):
        logger.info('Spark cluster is terminating...')

        threads: List[threading.Thread] = []
        for worker in self.workers:
            thread = threading.Thread(target=worker.terminate)
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()

        self.master.terminate()

        logger.info('Spark cluster has terminated.')

    def install_cloud_watch_agent(self):
        logger.debug('Spark cluster is installing cloudwatch agent...')
        threads: List[threading.Thread] = [threading.Thread(target=self.master.install_cloudwatch_agent)]
        for worker in self.workers:
            threads.append(threading.Thread(target=worker.install_cloudwatch_agent))
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        logger.debug('Spark cluster has finished installing cloudwatch agent.')

    def collect_cluster_info(self, output_dir: str = None):
        """Collect spark cluster information.

        :param output_dir:
        :return:
        """
        if not output_dir:
            output_dir = os.path.join(os.environ['RAVEN_HOME'], 'out', 'cluster', f'spark-{self._cluster_id}')
        os.makedirs(output_dir, exist_ok=True)
        info = {
            'Master': self.master.to_dict(),
            'Workers': [worker.to_dict() for worker in self.workers]
        }
        with open(os.path.join(output_dir, f'cluster-info_{time.strftime("%Y-%m-%d_%H-%M-%S")}.json'), mode='w',
                  encoding='utf-8') as file:
            json.dump(info, file, indent=2)

    def collect_metrics(self, output_dir: str = None):
        logger.debug('Spark cluster is pulling metrics cloudwatch agent...')
        if not output_dir:
            output_dir = os.path.join(os.environ['RAVEN_HOME'], 'out', 'cluster', f'spark-{self._cluster_id}')
        os.makedirs(output_dir, exist_ok=True)
        threads: List[threading.Thread] = [
            threading.Thread(target=self.master.collect_metrics, kwargs={'output_dir': output_dir})]
        for worker in self.workers:
            threads.append(threading.Thread(target=worker.collect_metrics, kwargs={'output_dir': output_dir}))
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        logger.debug('Spark cluster has finished pulling metrics cloudwatch agent...')