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

import logging.config
import os
import sys

import yaml
from benchmark.engine.athena.engine import Engine

if __name__ == '__main__':
    sys.path.append(os.environ['RAVEN_HOME'])
    os.chdir(os.environ['RAVEN_HOME'])

    # logging
    with open(os.path.join('configs', 'logging.yaml'), encoding='utf-8') as file:
        logging_config = yaml.load(file, Loader=yaml.FullLoader)
        logging.config.dictConfig(logging_config)

    engine = Engine()
    engine.launch()

    # 为 Athena 创建 TPC-DS 1G 的表
    with open(os.path.join('configs', 'workloads', 'tpcds-1g-athena.yaml'),
              encoding='utf-8') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
        database = config['Database']['Name']
        for table in config['Tables']:
            engine.execute_query(database, table['Create'])
