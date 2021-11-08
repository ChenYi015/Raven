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
import time

import yaml
from pyspark.conf import SparkConf
from pyspark.sql import SparkSession

from benchmark.core.engine import AbstractEngine


class Engine(AbstractEngine):

    def __init__(self):
        super().__init__()
        self._name = 'Spark-SQL'
        self._conf = SparkConf()
        with open(os.path.join('configs', 'engines', 'spark-sql.yaml'), encoding='utf-8') as file:
            config = yaml.load(file, yaml.FullLoader)
        for key, value in config['Config'].items():
            self._conf.set(key, value)
        self._conf.setAppName('Raven')
        self._session = None

    def launch(self):
        logging.info(f'{self._name} is launching...')
        self._session = SparkSession.builder \
            .config(conf=self._conf) \
            .enableHiveSupport() \
            .getOrCreate()
        logging.info(f'{self._name} has launched.')

    def execute_query(self, database: str, sql: str, name: str = None):
        logging.info(f'{self._name} is executing query: {name}.')

        start = time.time()
        try:
            self._session.sql(f'use {database}')
            result = self._session.sql(sql)
            result.show()
        except Exception:
            logging.error(f'An error occurred when executing {name}.')
        end = time.time()
        duration = end - start

        logging.info(f'Finish executing query {name}, {duration:.3f} seconds has elapsed.')
        return duration

    def shutdown(self):
        logging.info(f'{self._name} is shutting down...')
        self._session = None
        logging.info(f'{self._name} has shut down. ')
