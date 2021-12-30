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


class PrestoCoordinator(Ec2Instance):

    def __init__(self, *, aws: AmazonWebService = None, region: str = '', ec2_key_name: str = '',
                 ec2_instance_type: str):
        path = os.path.join(os.environ['RAVEN_HOME'], 'config', 'cloud', 'aws', 'presto',
                            'presto-coordinator-cloudformation-template.yaml')
        with open(path, encoding='utf-8') as file:
            template = file.read()

        super().__init__(
            name='PrestoCoordinator',
            aws=aws,
            region=region,
            stack_name='Raven-Presto-Coordinator-Stack',
            template=template,
            ec2_key_name=ec2_key_name,
            ec2_instance_type=ec2_instance_type
        )

    def launch(self):
        logger.info('Presto coordinator is launching...')
        super().launch()
        logger.info('Presto coordinator has launched.')

    def terminate(self):
        logger.info('Presto coordinator is terminating...')
        super().terminate()
        logger.info('Presto coordinator has terminated.')


class PrestoWorker(Ec2Instance):

    def __init__(self, *, aws: AmazonWebService = None, region: str = '', ec2_key_name: str = '',
                 ec2_instance_type: str, worker_id: int = 1):
        path = os.path.join(os.environ['RAVEN_HOME'], 'config', 'cloud', 'aws', 'presto',
                            'presto-worker-cloudformation-template.yaml')
        with open(path, encoding='utf-8') as file:
            template = file.read()

        super().__init__(
            name=f'PrestoWorker{worker_id}',
            aws=aws,
            region=region,
            stack_name=f'Raven-Presto-Worker{worker_id}-Stack',
            template=template,
            ec2_key_name=ec2_key_name,
            ec2_instance_type=ec2_instance_type,
            PrestoWorkerId=worker_id
        )

        self._worker_id = worker_id
        self._presto_coordinator_private_ip = ''

    @property
    def worker_id(self):
        return self._worker_id

    @property
    def presto_coordinator_private_ip(self):
        return self._presto_coordinator_private_ip

    @presto_coordinator_private_ip.setter
    def presto_coordinator_private_ip(self, private_ip: str):
        self._presto_coordinator_private_ip = private_ip
        self.kwargs['PrestoCoordinatorPrivateIp'] = private_ip

    def launch(self):
        logger.info(f'Presto worker {self._worker_id} is launching...')
        super().launch()
        logger.info(f'Presto worker {self._worker_id} has launched.')

    def terminate(self):
        logger.info(f'Presto worker {self._worker_id} is terminating...')
        super().terminate()
        logger.info(f'Presto worker {self._worker_id} has terminated.')


class PrestoCluster:

    def __init__(self, aws: AmazonWebService, master_instance_type: str = 't2.small', worker_num: int = 0,
                 worker_instance_type: str = 't2.small'):
        self._aws = aws
        self._coordinator = PrestoCoordinator(aws=aws, ec2_instance_type=master_instance_type)
        self._worker_instance_type = worker_instance_type
        self._workers: List[PrestoWorker] = [
            PrestoWorker(aws=aws, ec2_instance_type=worker_instance_type, worker_id=worker_id) for worker_id in
            range(0, worker_num)]
        self._cluster_id = get_random_id(16)

    @property
    def coordinator(self):
        return self._coordinator

    @property
    def workers(self):
        return self._workers

    def __str__(self):
        return f'PrestoCluster(Coordinator={self.coordinator}, #Worker={len(self.workers)})'

    def launch(self):
        logger.info('Presto cluster is launching...')

        self.coordinator.launch()

        threads: List[threading.Thread] = []
        for worker in self.workers:
            worker.presto_coordinator_private_ip = self.coordinator.private_ip
            thread = threading.Thread(target=worker.launch)
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()

        logger.info('Presto cluster has launched.')

    def scale(self, worker_num: int):
        logger.info('Presto cluster is scaling...')
        n = len(self.workers)
        threads: List[threading.Thread] = []
        if worker_num < n:
            for worker_id in range(worker_num, n):
                thread = threading.Thread(target=self.workers[worker_id].terminate)
                thread.start()
                threads.append(thread)
            self._workers = self._workers[:worker_num]
        elif worker_num > n:
            for worker_id in range(n, worker_num):
                worker = PrestoWorker(aws=self._aws, ec2_instance_type=self._worker_instance_type, worker_id=worker_id)
                worker.presto_coordinator_private_ip = self.coordinator.private_ip
                self.workers.append(worker)
                thread = threading.Thread(target=worker.launch)
                thread.start()
                threads.append(thread)
        for thread in threads:
            thread.join()
        logger.info('Presto cluster has finished scaling.')

    def terminate(self):
        logger.info('Presto cluster is terminating...')

        threads: List[threading.Thread] = []
        for worker in self.workers:
            thread = threading.Thread(target=worker.terminate)
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()

        self.coordinator.terminate()

        logger.info('Presto cluster has terminated.')

    def install_cloud_watch_agent(self):
        logger.debug('Presto cluster is installing cloudwatch agent...')
        threads: List[threading.Thread] = [threading.Thread(target=self.coordinator.install_cloudwatch_agent)]
        for worker in self.workers:
            threads.append(threading.Thread(target=worker.install_cloudwatch_agent))
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        logger.debug('Presto cluster has finished installing cloudwatch agent.')

    def collect_cluster_info(self, output_dir: str = None):
        """Collect presto cluster information.

        :param output_dir:
        :return:
        """
        if not output_dir:
            output_dir = os.path.join(os.environ['RAVEN_HOME'], 'out', 'cluster', f'presto-{self._cluster_id}')
        os.makedirs(output_dir, exist_ok=True)
        info = {
            'Coordinator': self.coordinator.to_dict(),
            'Workers': [worker.to_dict() for worker in self.workers]
        }
        with open(os.path.join(output_dir, f'cluster-info_{time.strftime("%Y-%m-%d_%H-%M-%S")}.json'), mode='w',
                  encoding='utf-8') as file:
            json.dump(info, file, indent=2)

    def collect_metrics(self, output_dir: str = None):
        logger.debug('Presto cluster is pulling metrics cloudwatch agent...')
        if not output_dir:
            output_dir = os.path.join(os.environ['RAVEN_HOME'], 'out', 'cluster', f'presto-{self._cluster_id}')
        os.makedirs(output_dir, exist_ok=True)
        threads: List[threading.Thread] = [
            threading.Thread(target=self.coordinator.collect_metrics, kwargs={'output_dir': output_dir})]
        for worker in self.workers:
            threads.append(threading.Thread(target=worker.collect_metrics, kwargs={'output_dir': output_dir}))
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        logger.debug('Presto cluster has finished pulling metrics cloudwatch agent...')
