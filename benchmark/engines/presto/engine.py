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

import prestodb

from benchmark.core.engine import AbstractEngine


class Engine(AbstractEngine):

    def __init__(self):
        super().__init__()
        self._cursor = None

    def launch(self):
        logging.info('Presto engine is launching...')
        logging.info('Presto engine has launched.')

    def execute_query(self, database: str, sql: str, name: str = None):
        self._cursor = prestodb.dbapi.connect(
            host='localhost',
            port=8889,
            user='hadoop',
            catalog='hive',
            schema=database
        ).cursor()

        try:
            start = time.time()
            logging.info(f'Now executing {name}...')
            self._cursor.execute(f'{sql}')
            self._cursor.fetchall()
            end = time.time()
            return end - start
        except Exception:
            logging.error(f'An error occurred when executing {name}.')
            return -1

    def shutdown(self):
        logging.info('Presto engine is shutting down...')
        self._cursor.close()
        self._cursor = None
        logging.info('Presto engine has shut down. ')
