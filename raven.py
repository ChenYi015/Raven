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
import threading
import time
from concurrent.futures.thread import ThreadPoolExecutor
from queue import Queue
from threading import Timer

import yaml

from benchmark.core.engine import AbstractEngine
from benchmark.core.testplan import Testplan
from benchmark.core.workload import Workload
from benchmark.pipeline.pipeline import Pipeline
from benchmark.testplans.timeline import Timeline, Event


class Raven:
    """
    Raven - a benchmark framework for olap engines within cloud.
    """

    def __init__(self):
        self.provider = None  # Cloud providers
        self.engine: AbstractEngine = None  # OLAP engine
        self.workload: Workload = None  # Workload
        self.plan = None  # Testplan
        self.collector = None  # Statistics collector

        self._hook_exec_pool = ThreadPoolExecutor(max_workers=12)

    def setup(self, config):
        # Setup engine
        logging.info('Raven is setting up engine...')
        engine_module = importlib.import_module(f'benchmark.engines.{config["Engine"]["Name"]}.engine')
        self.engine = engine_module.Engine(config['Engine'])
        self.engine.launch()

        # Setup testplan
        logging.info('Raven is setting up testplan...')
        plan_type = config['Testplan']['Properties']['Type']
        logging.info(f'Type of testplan: {plan_type}.')
        plan_path = os.path.join(os.environ['RAVEN_HOME'], *config['Testplan']['Properties']['Path'].split('/'))
        logging.info(f'Path of testplan config file: {plan_path}.')
        if plan_type == Testplan.Type.PIPELINE:
            pass
        elif plan_type == Testplan.Type.TIMELINE:
            logging.info('Raven is setting up timeline...')
            with open(plan_path, encoding='utf-8') as stream:
                plan_config = yaml.load(stream, yaml.FullLoader)
                self.plan = Timeline(plan_config)

        # Setup workload
        logging.info('Raven is setting up workload...')
        with open(os.path.join(os.environ['RAVEN_HOME'], 'configs', 'workloads',
                               f'{config["Workload"]["Name"]}', 'workload.yaml')) as _:
            workload_config = yaml.load(_, yaml.FullLoader)
            self.workload = Workload(workload_config)

        # TODO: Setup metrics
        logging.info('Raven is setting up metrics...')

    # def generate_testplan(self):
    #     logging.info("Generating execution plan...")
    #
    #     logging.info('Generating execution plan successfully!')

    def start(self):
        if self.plan.type == Testplan.Type.PIPELINE:
            self._execute_pipeline(self.plan)
        elif self.plan.type == Testplan.Type.TIMELINE:
            self._execute_timeline(self.plan)

    def stop(self):
        # 停止查询引擎
        self.engine.shutdown()

    def _execute_pipeline(self, plan: Pipeline):
        # database = workload['Database']
        # for query in workload['Queries']:
        #     self.engine.execute_query(database, query['SQL'])
        pass

    def _handle_stage(self, stage):
        pass

    def _execute_timeline(self, timeline: Timeline):
        logging.info(f'Raven is executing timeline: {timeline.name}...')
        # 给 Workload 中的每个事件设置一个定时器
        # 定时器触发时调用相应事件的 hook 处理事件
        threads = [Timer(event.time, self._handle_event, args=(event,)) for event in timeline.events]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        logging.info('Main thread completes.')

    def _handle_event(self, event: Event):
        """
        根据事件名称调用相应的 hook 进行处理.
        :param event:
        :return:
        """
        logging.info(f'Raven is handling event: {event.name}...')
        hook_module = importlib.import_module(f'benchmark.engines.{self.engine.name.lower()}.hooks.{event.name}')
        future = self._hook_exec_pool.submit(hook_module.hook, self.engine)

        # 查询开始
        if event.name == Event.Name.ON_QUERY_START:
            with open(os.path.join(os.environ['RAVEN_HOME'], 'configs', 'workloads', self.workload.name,
                                   'query_script.yaml'), encoding='utf-8') as stream:
                query_script = yaml.load(stream, yaml.FullLoader)

            # 查询开始时刻
            query_start = time.time()

            # 查询用例采用生产者消费者模式
            # workload 是生产者, engine 是消费者
            # 生产者和消费者之间通过查询请求队列进行通信
            query_queue = Queue()

            # workload 启动若干个线程用于生成查询请求至请求队列
            threading.Thread(target=self.workload.generate_random_queries, args=(query_queue,)).start()

            # engine 启动若干个线程用于处理查询请求
            threading.Thread(target=self.engine.execute_queries, args=(query_queue,)).start()


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
