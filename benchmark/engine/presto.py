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

import prestodb

import configs
from benchmark.core.engine import Engine
from benchmark.core.query import Query, QueryStatus

logger = configs.EXECUTE_LOGGER


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
            query.status = QueryStatus.RUNNING
            cursor.execute(f'{query.sql}')
            cursor.fetchone()
            cursor.close()
            query.status = QueryStatus.SUCCEEDED
            logger.info(f'{self.name} has finished executing {query}.')
        except Exception as error:
            query.status = QueryStatus.FAILED
            logger.error(f'{self.name} failed to execute_queries {query}, an error has occurred: {error}')
        return query
