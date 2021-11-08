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

import yaml


def engine_test(engine_name: str, workload_name: str):
    engine_module = importlib.import_module(f'benchmark.engines.{engine_name}.engine')
    engine = engine_module.Engine()
    engine.launch()
    with open(os.path.join('configs', 'workloads', f'{workload_name}.yaml'), encoding='utf-8') as file:
        workload = yaml.load(file, yaml.FullLoader)
    database = workload['Database']
    for query in workload['Queries']:
        sql = query['SQL']
        name = query['Name']
        engine.execute_query(database=database, sql=sql, name=name)


if __name__ == '__main__':
    import sys
    import os
    sys.path.append(os.path.join('home', 'hadoop', 'Raven'))
    engine_name = 'spark_sql'
    workload_name = 'tpcds-1g'
    engine_test(engine_name, workload_name)
