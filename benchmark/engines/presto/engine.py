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
from benchmark.core.engine import AbstractEngine
from benchmark.core.query import Query, Status

logger = configs.EXECUTE_LOGGER


class Engine(AbstractEngine):

    def __init__(self, config: dict):
        super().__init__(config)

    def launch(self):
        logger.info('Presto engine is launching...')
        logger.info('Presto engine has launched.')

    def execute_query(self, query: Query) -> Query:
        logger.info(f'{self.name} engine is executing query: {query}.')

        try:
            cursor = prestodb.dbapi.connect(
                host='localhost',
                port=8889,
                user='hadoop',
                catalog='hive',
                schema=query.database
            ).cursor()
            query.set_status(Status.EXECUTE)
            cursor.execute(f'{query.sql}')
            cursor.fetchone()
            cursor.close()
            query.set_status(Status.FINISH)
            logger.info(f'{self.name} engine has finished executing query: {query}.')
        except Exception as e:
            query.set_status(Status.FAIL)
            logger.error(f'{self.name} engines failed to execute query: {query}, an error has occurred: {e}')
        return query

    def shutdown(self):
        logger.info('Presto engine is shutting down...')
        logger.info('Presto engine has shut down. ')
