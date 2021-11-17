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
import time

from pyhive import hive
from pyhive.exc import OperationalError

import configs
from benchmark.core.engine import AbstractEngine
from benchmark.core.query import Query, Status

logger = configs.EXECUTE_LOGGER


class Engine(AbstractEngine):

    def __init__(self, config: dict):
        super().__init__(config)
        self._cursor = None

    def launch(self):
        logger.info('Hive engine is launching...')
        self._cursor = hive.connect('localhost').cursor()
        logger.info('Hive engine has launched...')

    def execute_query(self, query: Query):
        logger.debug(f'{self.name} engine is executing query: {query}.')
        query.set_status(Status.EXECUTE)
        try:
            self._cursor.execute(f'use {query.database}')
            self._cursor.execute(f'{query.sql}')
            self._cursor.fetchall()
            # print(self._cursor.fetch_logs())

            query.set_status(Status.FINISH)
            logger.info(f'{self.name} engine has finished executing query: {query}.')
        except OperationalError:
            query.set_status(Status.FAIL)
            logger.error(f'{self.name} engines failed to execute query {query}, an error has occurred: {e}')

    def shutdown(self):
        self._cursor.close()
        self._cursor = None
