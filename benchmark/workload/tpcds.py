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
from typing import List

import yaml

from benchmark.core.query import Query
from benchmark.core.workload import LoopWorkload, QpsWorkload

TPCDS_QUERIES: List[Query] = []
with open(os.path.join(os.environ['RAVEN_HOME'], 'config', 'workload', 'tpcds.yaml'),
          encoding='utf-8') as file:
    workload_config: dict = yaml.load(file, Loader=yaml.FullLoader)
for query_config in workload_config['Queries']:
    TPCDS_QUERIES.append(Query(name=query_config.get('Name', ''), description=query_config.get('Description', ''),
                               database=query_config['Database'], sql=query_config['Sql']))


class TpcdsLoopWorkload(LoopWorkload):

    def __init__(self):
        name = 'TPC-DS Loop Workload'
        description = 'TPC-DS Workload which can generate multiple loops of queries.'
        super().__init__(name=name, description=description)
        for query in TPCDS_QUERIES:
            self.append_query(query)


class TpcdsQpsWorkload(QpsWorkload):

    def __init__(self):
        name = 'TPC-DS QPS Workload'
        description = 'TPC-DS Workload which qps varies with diverse distributions as time goes on..'
        super().__init__(name=name, description=description)
        for query in TPCDS_QUERIES:
            self.append_query(query)
