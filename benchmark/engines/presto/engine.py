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

import prestodb

from benchmark.core.engine import AbstractEngine
from benchmark.core.query import Query, Status


class Engine(AbstractEngine):

    def __init__(self, config: dict):
        super().__init__(config)
        self._cursor = None

    def launch(self):
        logging.info('Presto engine is launching...')
        logging.info('Presto engine has launched.')

    def execute_query(self, query: Query):
        logging.debug(f'{self.name} engine is executing query: {query}.')
        query.set_status(Status.EXECUTE)

        try:
            self._cursor = prestodb.dbapi.connect(
                host='localhost',
                port=8889,
                user='hadoop',
                catalog='hive',
                schema=query.database
            ).cursor()

            self._cursor.execute(f'{query.sql}')
            self._cursor.fetchall()
            query.set_status(Status.FINISH)
            logging.info(f'{self.name} engine has finished executing query: {query}.')
        except Exception as e:
            query.set_status(Status.FAIL)
            logging.error(f'{self.name} engines failed to execute query: {query}, an error has occurred: {e}')

    def shutdown(self):
        logging.info('Presto engine is shutting down...')
        self._cursor.close()
        self._cursor = None
        logging.info('Presto engine has shut down. ')
