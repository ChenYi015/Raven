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

import yaml
from pyspark.conf import SparkConf
from pyspark.sql import SparkSession

from benchmark.core.engine import AbstractEngine
from benchmark.core.query import Query, Status


class Engine(AbstractEngine):

    def __init__(self, config: dict):
        super().__init__(config)
        self._name = 'Spark-SQL'
        self._conf = SparkConf()
        with open(os.path.join(os.environ['RAVEN_HOME'], 'configs', 'engines', 'spark_sql', 'spark-sql.yaml'), encoding='utf-8') as file:
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

    def execute_query(self, query: Query):
        logging.debug(f'{self.name} engine is executing query: {query}.')
        query.set_status(Status.EXECUTE)
        try:
            self._session.sql(f'use {query.database}')
            result = self._session.sql(query.sql)
            result.show()
            query.set_status(Status.FINISH)
            logging.info(f'{self.name} engine has finished executing query: {query}.')
        except Exception as e:
            query.set_status(Status.FAIL)
            logging.error(f'{self.name} engines failed to execute query {query}, an error has occurred: {e}')

    def shutdown(self):
        logging.info(f'{self._name} is shutting down...')
        self._session = None
        logging.info(f'{self._name} has shut down. ')
