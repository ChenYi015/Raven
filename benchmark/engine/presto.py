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
import threading
from typing import List

import prestodb

import configs
from benchmark.cloud.aws import AmazonWebService, Ec2Instance
from benchmark.core.engine import Engine
from benchmark.core.query import Query, Status

logger = configs.EXECUTE_LOGGER


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

    def __str__(self):
        return f'{self.name}(PublicIp={self.public_ip}, PrivateIp={self.private_ip})'

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

    def __str__(self):
        return f'{self.name}(PublicIp={self.public_ip}, PrivateIp={self.private_ip})'

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
        self._coordinator = PrestoCoordinator(aws=aws, ec2_instance_type=master_instance_type)
        self._workers: List[PrestoWorker] = [
            PrestoWorker(aws=aws, ec2_instance_type=worker_instance_type, worker_id=worker_id) for worker_id in
            range(1, worker_num + 1)]

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


class PrestoEngine(Engine):

    def __init__(self, *, host: str = 'localhost', port: int = 8080, user='hive', catalog='hive', concurrency: int = 1):
        super().__init__(name='Presto', description='Presto OLAP engine.', concurrency=concurrency)
        self.host = host
        self.port = port
        self.user = user
        self.catalog = catalog

    def execute_query(self, query: Query) -> Query:
        logger.info(f'{self.name} is executing {query}.')

        try:
            cursor = prestodb.dbapi.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                catalog=self.catalog,
                schema=query.database
            ).cursor()
            query.status = Status.RUNNING
            cursor.execute(f'{query.sql}')
            cursor.fetchone()
            cursor.close()
            query.status = Status.SUCCEEDED
            logger.info(f'{self.name} has finished executing {query}.')
        except Exception as error:
            query.status = Status.FAILED
            logger.error(f'{self.name} failed to execute_queries {query}, an error has occurred: {error}')
        return query
