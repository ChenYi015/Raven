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

from pyspark.sql import SparkSession

import configs
from benchmark.cloud.aws import Ec2Instance, AmazonWebService
from benchmark.core.engine import Engine
from benchmark.core.query import Query, Status

logger = configs.EXECUTE_LOGGER


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
        self._spark_master_url = ''

    @property
    def spark_master_url(self):
        return self._spark_master_url

    def __str__(self):
        return f'{self.name}(PublicIp={self.public_ip}, PrivateIp={self.private_ip})'

    def launch(self):
        logger.info('Spark master is launching...')
        super().launch()
        self._spark_master_url = self.aws.get_stack_output_by_key(stack_name=self.stack_name,
                                                                  output_key='SparkMasterUrl')
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
        self._spark_master_url = ''

    @property
    def worker_id(self):
        return self._worker_id

    @property
    def spark_master_url(self):
        return self._spark_master_url

    @spark_master_url.setter
    def spark_master_url(self, url: str):
        self._spark_master_url = url
        self.kwargs['SparkMasterUrl'] = url

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
            worker.spark_master_url = self.master.spark_master_url
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


class SparkSqlEngine(Engine):

    def __init__(self, *, concurrency: int = 1):
        super().__init__(name='SparkSQL', description='Spark SQL.', concurrency=concurrency)
        self._session = SparkSession.builder \
            .enableHiveSupport() \
            .getOrCreate()

    def execute_query(self, query: Query) -> Query:
        logger.info(f'{self.name} is executing {query}.')
        try:
            self._session.catalog.setCurrentDatabase(query.database)
            query.status = Status.RUNNING
            self._session.sql(query.sql).show()
            query.status = Status.SUCCEEDED
            logger.info(f'{self.name} has finished executing {query}.')
        except Exception as error:
            query.status = Status.FAILED
            logger.error(f'{self.name} failed to execute_queries {query}, an error has occurred: {error}')
        return query

    def shutdown(self):
        logger.info(f'{self.name} is shutting down...')
        self._session.stop()
        logger.info(f'{self.name} has shut down. ')
