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

import os
import sys

import yaml
from pyspark.conf import SparkConf
from pyspark.sql import SparkSession

import configs
from benchmark.core.engine import AbstractEngine
from benchmark.core.query import Query, Status

logger = configs.EXECUTE_LOGGER


class Engine(AbstractEngine):

    def __init__(self, config: dict):
        super().__init__(config)
        self._name = 'Spark-SQL'
        self._conf = SparkConf()
        with open(os.path.join(os.environ['RAVEN_HOME'], 'configs', 'engines', 'spark_sql', 'spark-sql.yaml'),
                  encoding='utf-8') as file:
            config = yaml.load(file, yaml.FullLoader)
        for key, value in config['Config'].items():
            self._conf.set(key, value)

        os.environ['HADOOP_HOME'] = os.path.join('/', 'usr', 'lib', 'hadoop')
        os.environ['HADOOP_CONF_DIR'] = os.path.join('/', 'etc', 'hadoop', 'conf')
        os.environ['HIVE_CONF_DIR'] = os.path.join('/', 'etc', 'hive', 'conf')
        os.environ['YARN_CONF_DIR'] = os.path.join('/', 'etc', 'hadoop', 'conf')
        os.environ['SPARK_HOME'] = os.path.join('/', 'usr', 'lib', 'spark')

        sys.path.append(os.path.join(os.environ['SPARK_HOME'], "bin"))
        sys.path.append(os.path.join(os.environ['SPARK_HOME'], "python"))
        sys.path.append(os.path.join(os.environ['SPARK_HOME'], "python", "pyspark"))
        sys.path.append(os.path.join(os.environ['SPARK_HOME'], "python", "lib"))
        sys.path.append(os.path.join(os.environ['SPARK_HOME'], "python", "lib", "pyspark.zip"))
        sys.path.append(os.path.join(os.environ['SPARK_HOME'], "python", "lib", "py4j-src.zip"))
        self._session = SparkSession.builder \
            .enableHiveSupport() \
            .getOrCreate()

    def launch(self):
        logger.info(f'{self._name} is launching...')
        logger.info(f'{self._name} has launched.')

    def execute_query(self, query: Query) -> Query:
        logger.info(f'{self.name} engine is executing query: {query}.')
        try:
            self._session.catalog.setCurrentDatabase(query.database)
            query.set_status(Status.EXECUTE)
            self._session.sql(query.sql).show()
            query.set_status(Status.FINISH)
            logger.info(f'{self.name} engine has finished executing query: {query}.')
        except Exception as e:
            query.set_status(Status.FAIL)
            logger.error(f'{self.name} engines failed to execute query {query}, an error has occurred: {e}')
        return query

    def shutdown(self):
        logger.info(f'{self._name} is shutting down...')
        self._session.stop()
        logger.info(f'{self._name} has shut down. ')
