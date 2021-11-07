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

from pyspark.conf import SparkConf
from pyspark.sql import SparkSession

from benchmark.core.engine import AbstractEngine


class Engine(AbstractEngine):

    def __init__(self):
        super().__init__()
        self._session = None

    def launch(self):
        logging.info('Spark-SQL is launching...')
        self._session = SparkSession.builder \
            .appName('Raven') \
            .config(conf=SparkConf()) \
            .enableHiveSupport() \
            .getOrCreate()
        logging.info('Spark-SQL has launched.')

    def execute_query(self, database: str, sql: str, name: str = None):
        if self._session is not None:
            logging.info(f'Start to execute query: {sql}.')
            start = time.time()
            self._session.sql(sql).show()
            end = time.time()
            duration = end - start
            logging.info(f'Finish executing query {name}, {duration:.3f} seconds has elapsed.')
            return duration
        else:
            logging.warning('Spark-SQL failed to execute query: no spark session specified.')
            return -1

    def shutdown(self):
        self._session = None
