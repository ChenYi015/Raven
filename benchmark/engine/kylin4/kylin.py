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

import requests

from benchmark.core.engine import Engine
from benchmark.core.query import Query, Status

logger = logging.getLogger()


class KylinHttpClient:

    def __init__(self, host, port):
        self._session: requests.Session = requests.Session()
        self._base_url: str = f'http://{host}:{port}'
        self._headers = {
            'Accept': 'application/json',
            'Accept-Language': 'en-US',
            'Content-Type': 'application/json;charset=utf-8'
        }

    def _request(self, method: str, url: str, **kwargs):
        response = self._session.request(method, self._base_url + url, **kwargs)
        return response

    def login(self, username: str, password: str):
        url = '/kylin/api/user/authentication'
        self._session.auth = (username, password)
        try:
            response = self._request('POST', url)
            return response
        except Exception as error:
            logging.error(f'{error}')

    def _check_login_state(self):
        url = '/kylin/api/user/authentication'
        response = self._request('GET', url)
        return response

    def describe_cube(self, cube_name: str):
        pass

    def build_cube(self, cube_name: str):
        pass

    def get_job_status(self, job_uuid: str):
        pass

    def resume_job(self, job_uuid: str):
        pass

    def execute_query(self, project: str, sql: str, offset: int = 0, limit: int = 500, accept_partial=False,
                      timeout=360):
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
        self._http_client.login(username='KYLIN', password='ADMIN')

    def execute_query(self, query: Query) -> Query:
        logger.info(f'{self.name} is executing {query}.')
        try:
            # FIXME
            response = self._http_client.execute_query(
                project=query.database,
                sql=query.sql,
                limit=10
            )
            query.status = Status.RUNNING
            query.status = Status.SUCCEEDED
            logger.info(f'{self.name} has finished executing {query}.')
        except Exception as error:
            query.status = Status.FAILED
            logger.error(f'{self.name} failed to execute_queries {query}, an error has occurred: {error}')
        return query

