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

from pyspark.sql import SparkSession

import configs
from benchmark.core.engine import Engine
from benchmark.core.query import Query, Status

logger = configs.EXECUTE_LOGGER


class SparkSqlEngine(Engine):

    def __init__(self, *, concurrency: int = 1):
        super().__init__(name='SparkSQL', description='Spark SQL.', concurrency=concurrency)
        self._session = SparkSession.builder \
            .enableHiveSupport() \
            .getOrCreate()

    def launch(self):
        logger.info(f'{self.name} is launching...')
        logger.info(f'{self.name} has launched.')

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
