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

from benchmark.core.engine import AbstractEngine


class Engine(AbstractEngine):

    def __init__(self):
        super().__init__()
        self._cursor = None

    def launch(self):
        logging.info('Hive engine is launching...')
        self._cursor = hive.connect('localhost').cursor()
        logging.info('Hive engine has launched...')

    def execute_query(self, database: str, sql: str, name: str = None):
        self._cursor.execute(f'use {database}')
        try:
            print(f'Now executing {name}...')
            # logging.info(f'Start to execute query: {sql}.')
            start = time.time()
            self._cursor.execute(f'{sql}')
            end = time.time()
            duration = end - start
            logging.info(f'Finish executing query {name}, {duration:.3f} seconds has elapsed.')
            self._cursor.fetchall()
            # print(self._cursor.fetch_logs())
        except OperationalError:
            print(f'An error occurred when executing {name}.')

    def shutdown(self):
        self._cursor.close()
        self._cursor = None
