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
from concurrent.futures.thread import ThreadPoolExecutor
from threading import Timer

import yaml

from benchmark.core.workload import WorkloadType, Event, Workload, TimelineWorkload, PipelineWorkload


class Raven:
    """
    Raven - a benchmark framework for olap engines within cloud.
    """

    def __init__(self):
        self.provider = None   # Cloud providers
        self.engine = None     # OLAP engine
        self.workload = None   # Workload
        self.plan = None       # Execution plan
        self.collector = None  # Statistics collector

        self._hook_exec_pool = ThreadPoolExecutor(max_workers=12)

    def setup(self, config):
        provider_config = config['Provider']

        engine_config = config['Engine']
        engine_module = importlib.import_module('benchmark.engines.{engine_name}.engine'.format(
            engine_name=engine_config['Name']))
        self.engine = engine_module.Engine()
        self.engine.launch()
        self.workload_config = config['Workload']
        with open(os.path.join('configs', 'workloads', '{workload_name}.yaml'.format(
                workload_name=self.workload_config['Name']), )) as _:
            self.workload = yaml.load(_, yaml.FullLoader)
        workload_config = config['Workload']
        with open(os.path.join('configs', 'workloads', '{workload_name}.yaml'.format(
                workload_name=workload_config['Name']), )) as _:
            self.workload = yaml.load(_, yaml.FullLoader)

    def generate_execution_plan(self):
        logging.info("Generating execution plan...")

        logging.info('Generating execution plan successfully!')

    def start(self):
        # 调用查询引擎执行工作负载
        if self.workload.type == Workload.Type.PIPELINE:
            self._execute_pipeline_workload(self.workload)
        elif self.workload.type == Workload.Type.TIMELINE:
            self._execute_timeline_workload(self.workload)

    def stop(self):
        # 停止查询引擎
        self.engine.shutdown()

    def _execute_pipeline_workload(self, workload: PipelineWorkload):
        database = workload['Database']
        for query in workload['Queries']:
            self.engine.execute_query(database, query['SQL'])

    def _handle_stage(self, stage):
        pass

    def _execute_timeline_workload(self, workload: TimelineWorkload):
        logging.info(f'Start executing timeline-based workload {workload.name}...')
        # 给 Workload 中的每个事件设置一个定时器
        # 定时器触发时调用相应事件的 hook 处理事件
        for event in workload.events:
            thread = Timer(event.time, self._handle_event, event)
            thread.start()
        logging.info('Main thread completes.')

    def _handle_event(self, event: Event):
        """
        根据事件名称调用相应的 hook 进行处理.
        :param event:
        :return:
        """
        hook_module = importlib.import_module(f'benchmark.hooks.{event.name}')
        future = self._hook_exec_pool.submit(hook_module.hook, self.engine)


if __name__ == '__main__':
    # Logging
    with open(os.path.join(os.environ['RAVEN_HOME'], 'configs', 'logging.yaml'), encoding='utf-8') as file:
        logging_config = yaml.load(file, Loader=yaml.FullLoader)
        logging.config.dictConfig(logging_config)

    # Raven
    raven = Raven()
    with open(os.path.join(os.environ['RAVEN_HOME'], 'configs', 'raven.yaml'), encoding='utf-8') as file:
        raven_config = yaml.load(file, Loader=yaml.FullLoader)
        raven.setup(raven_config)
    raven.start()
    raven.stop()
