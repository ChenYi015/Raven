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
import os

import yaml


class Raven:
    """
    Raven - a benchmark framework for olap engines within cloud.
    """

    def __init__(self):
        with open(os.path.join('.', 'configs', 'config.yaml'), encoding='utf-8') as file:
            config = yaml.load(file, Loader=yaml.FullLoader)
        self._provider = None
        self._engine_name = config['Engine']['Name']
        self._engine_module = importlib.import_module(f'benchmark.engines.{self._engine_name}.engine')
        self._engine = self._engine_module.Engine()
        self._engine.launch()

        workload_name = config['Workload']['Name']
        with open(os.path.join('.', 'configs', 'workloads', f'{workload_name}.yaml'), encoding='utf-8') as file:
            self._workload = yaml.load(file, Loader=yaml.FullLoader)

    def run(self):
        # 调用查询引擎执行工作负载
        if self._workload['Type'] == 'pipeline':
            self._execute_pipeline(self._workload)
        elif self._workload['Type'] == 'timeline':
            self._execute_timeline(self._workload)

        # 停止查询引擎
        self._engine.shutdown()

    def _execute_pipeline(self, pipeline):
        database = pipeline['Database']
        for query in pipeline['Queries']:
            self._engine.execute_query(database, query)

    def _execute_timeline(self, timeline):
        pass


if __name__ == '__main__':
    raven = Raven()
    raven.run()
