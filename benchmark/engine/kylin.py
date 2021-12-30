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

import requests

from benchmark.cloud.aws import Ec2Instance, AmazonWebService
from benchmark.core.engine import Engine
from benchmark.core.query import Query, Status

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
        self._master = KylinMaster(aws=aws, ec2_instance_type=master_instance_type)
        self._workers: List[KylinWorker] = [
            KylinWorker(aws=aws, ec2_instance_type=worker_instance_type, worker_id=worker_id) for worker_id in
            range(1, worker_num + 1)]

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
            worker.spark_master_url = self.master.spark_master_url
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

    def scale_workers(self, worker_num: int):
        pass


class KylinHttpClient:

    def __init__(self, host, port):
        self._session: requests.Session = requests.Session()
        self._base_url: str = f'http://{host}:{port}'
        self._headers = {
            'Accept': 'application/json',
            'Accept-Language': 'en-US',
            'Content-Type': 'application/json;charset=utf-8'
        }

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        response = self._session.request(method, self._base_url + url, **kwargs)
        return response

    def login(self, username: str, password: str) -> requests.Response:
        url = '/kylin/api/user/authentication'
        self._session.auth = (username, password)
        try:
            response = self._request('POST', url)
            response.raise_for_status()
            logger.debug(f'Kylin http client has successfully login.')
            return response
        except requests.exceptions.RequestException as error:
            logger.error(f'Kylin http client failed to login: {error}.')

    def describe_cube(self, cube_name: str, limit: int = 15, offset: int = 0):
        url = f'/kylin/api/cubes?cubeName={cube_name}&limit={limit}&offset={offset}'
        try:
            response = self._request('GET', url)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as error:
            logger.error(f'Kylin http client failed to describe cube {cube_name}: {error}.')

    def build_cube(self, cube_name: str):
        url = f'/kylin/api/cubes/{cube_name}/rebuild'
        try:
            response = self._request('PUT', url)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as error:
            logger.error(f'Kylin http client failed to build cube {cube_name}: {error}.')

    def get_job_status(self, job_uuid: str):
        url = '/kylin/api/jobs/{job_uuid}'
        try:
            response = self._request('GET', url)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as error:
            logger.error(f'Kylin http client failed to get status of job {job_uuid}: {error}.')

    def resume_job(self, job_uuid: str):
        url = '/kylin/api/jobs/{job_uuid}/resume'
        try:
            response = self._request('PUT', url)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as error:
            logger.error(f'Kylin http client failed to resume job {job_uuid}: {error}.')

    def optimize_cube(self, cube_name: str):
        url = f'/kylin/api/cubes/{cube_name}/optimize2'
        try:
            response = self._request('PUT', url)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as error:
            logger.error(f'Kylin http client failed to optimize cube {cube_name}: {error}.')

    def submit_query(self, *, project: str = 'Default', sql: str, offset: int = 0, limit: int = 100, accept_partial: bool = False,
                     timeout=360):
        """Submit query request to kylin.

        :param project: Project to perform query
        :param sql: The text of sql statement
        :param offset: Query offset
        :param limit: Query limit
        :param accept_partial: Whether accept a partial result or not.
        :param timeout: Request timeout limit.
        :return:
        """
        url = '/kylin/api/query'
        payload = {
            'limit': limit,
            'offset': offset,
            'project': project,
            'acceptPartial': accept_partial,
            'sql': sql,
        }
        response = self._request('POST', url, json=payload, timeout=timeout)
        return response


class KylinEngine(Engine):

    def __init__(self, *, concurrency: int = 1, host: str = 'localhost', port: int = 7070):
        super().__init__(name='Kylin Engine', description='Kylin 4.0.0 OLAP engine.', concurrency=concurrency)
        self._http_client = KylinHttpClient(host, port)
        self._http_client.login(username='ADMIN', password='KYLIN')

    def execute_query(self, query: Query) -> Query:
        logger.info(f'{self.name} is executing {query}.')
        try:
            # FIXME
            response = self._http_client.submit_query(
                project=query.database,
                sql=query.sql,
                limit=10
            )
            response.raise_for_status()
            query.status = Status.RUNNING
            query.status = Status.SUCCEEDED
            logger.info(f'{self.name} has finished executing {query}.')
        except requests.exceptions.HTTPError as error:
            query.status = Status.FAILED
            logger.error(f'{self.name} failed to execute_queries {query}, an error has occurred: {error}')
        return query
