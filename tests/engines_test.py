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

import importlib
import logging.config
import os
import sys

import yaml


def engine_test(engine_name: str, workload_name: str):
    engine_module = importlib.import_module(f'benchmark.engines.{engine_name}.engine')
    engine = engine_module.Engine()
    engine.launch()
    with open(os.path.join('configs', 'workloads', f'{workload_name}.yaml'), encoding='utf-8') as file:
        workload = yaml.load(file, yaml.FullLoader)
    database = workload['Database']['Name'] + '_1g'
    for query in workload['Queries']:
        sql = query['SQL']
        name = query['Name']
        engine.execute_query(database=database, sql=sql, name=name)


if __name__ == '__main__':
    sys.path.append(os.environ['RAVEN_HOME'])
    os.chdir(os.environ['RAVEN_HOME'])

    # logging
    with open(os.path.join('configs', 'logging.yaml'), encoding='utf-8') as file:
        logging_config = yaml.load(file, Loader=yaml.FullLoader)
        logging.config.dictConfig(logging_config)

    # TPC-DS(hybrid) with Spark-SQL
    # engine_test('spark_sql', 'tpcds-hybrid')

    # TPC-DS(hybrid) with Athena
    engine_test('athena', 'tpcds-hybrid')
