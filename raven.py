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

import yaml


class Raven:
    """
    Raven - a benchmark framework for olap engines within cloud.
    """

    def __init__(self):
<<<<<<< HEAD
        self._provider = None   # Cloud provider
        self._engine = None     # OLAP engine
        self._workload = None   # Workload
        self._plan = None       # Execution plan
        self._collector = None  # Statistics collector

    def setup(self, config):
        provider_config = config['Provider']

        engine_config = config['Engine']
        engine_module = importlib.import_module('benchmark.engines.{engine_name}.engine'.format(
            engine_name=engine_config['Name']))
        self._engine = engine_module.Engine()
=======
        self._provider_config = None
        self._engine_config = None
        self._engine_module = None
        self._engine = None
        self._workload_config = None
        self._workload = None

    def setup(self, config):
        self._provider_config = config['Provider']
        self._engine_config = config['Engine']
        self._engine_module = importlib.import_module('benchmark.engines.{engine_name}.engine'.format(
            engine_name=self._engine_config['Name']))
        self._engine = self._engine_module.Engine()
>>>>>>> 6cc2ae4288b75d4d38c2fbbbb66377228d7c338e
        self._engine.launch()
        self._workload_config = config['Workload']
        with open(os.path.join('configs', 'workloads', '{workload_name}.yaml'.format(
                workload_name=self._workload_config['Name']), )) as _:
            self._workload = yaml.load(_, yaml.FullLoader)

<<<<<<< HEAD
        workload_config = config['Workload']
        with open(os.path.join('configs', 'workloads', '{workload_name}.yaml'.format(
                workload_name=workload_config['Name']), )) as _:
            self._workload = yaml.load(_, yaml.FullLoader)

        # self._plan =

    def generate_execution_plan(self):
        logging.info("Generating execution plan...")

        logging.info('Generating execution plan successfully!')

    def start(self):

=======
    def generate(self):
        # Generate the workload
        pass
>>>>>>> 6cc2ae4288b75d4d38c2fbbbb66377228d7c338e

        # 调用查询引擎执行工作负载
        if self._workload['Type'] == 'Pipeline':
            self._execute_pipeline(self._workload)
        elif self._workload['Type'] == 'Timeline':
            self._execute_timeline(self._workload)


    def stop(self):
        # 停止查询引擎
        self._engine.shutdown()

    def _execute_pipeline(self, pipeline):
        database = pipeline['Database']
        for query in pipeline['Queries']:
            self._engine.execute_query(database, query['SQL'])

    def _execute_timeline(self, timeline):
        pass


if __name__ == '__main__':
    # Logging
    with open(os.path.join('configs', 'logging.yaml'), encoding='utf-8') as file:
        logging_config = yaml.load(file, Loader=yaml.FullLoader)
        logging.config.dictConfig(logging_config)

    # Raven
    raven = Raven()
    with open(os.path.join('configs', 'config.yaml'), encoding='utf-8') as file:
        raven_config = yaml.load(file, Loader=yaml.FullLoader)
        raven.setup(raven_config)
<<<<<<< HEAD
    raven.start()
    raven.stop()
=======
    raven.run()
>>>>>>> 6cc2ae4288b75d4d38c2fbbbb66377228d7c338e
