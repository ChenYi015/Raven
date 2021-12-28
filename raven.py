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
import queue
import threading
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import datetime
from threading import Timer

import yaml

import configs
from benchmark.core.engine import Engine
from benchmark.core.statistic import Collector
from benchmark.core.testplan import Testplan
from benchmark.core.workload import Workload
from benchmark.engine.manager import EngineManager
from benchmark.hook.manager import HookManager
from benchmark.pipeline.pipeline import Pipeline
from benchmark.testplan.timeline import Timeline, Event
from benchmark.workload.manager import WorkloadManager

logger = configs.ROOT_LOGGER


class Raven:
    """
    Raven - a benchmark framework for olap engines within cloud.
    """

    def __init__(self, config):
        self.config = config
        self.cloud = None  # Cloud providers
        self.engine: Engine = None  # OLAP engine
        self.workload: Workload = None  # Workload
        self.plan: Testplan= None  # Testplan
        self.collector: Collector = None  # Statistics collector

        self._hook_exec_pool = ThreadPoolExecutor(max_workers=12, thread_name_prefix='HookExecutor')

    def run(self):
        if self.plan.type == Testplan.Type.PIPELINE:
            self._execute_pipeline(self.plan)
        elif self.plan.type == Testplan.Type.TIMELINE:
            self._execute_timeline(self.plan)

    def setup_cloud(self):

    def setup_engine(self, engine_name, **kwargs):
        logger.info('Raven is setting up engine...')
        self.engine = EngineManager.get_engine(engine_name, **kwargs)
        self.engine.launch()

    def setup_workload(self, workload_name: str, workload_type: str, **kwargs):
        logger.info('Raven is setting up workload...')
        self.workload = WorkloadManager.get_workload(workload_name, workload_type)
        if 'Database' in kwargs:
            self.workload.set_database(database=kwargs['Database'])

    def setup_testplan(self, plan_type: str, plan_path: str):
        logger.info(f'Raven is setting up testplan, type: {plan_type}, path: {plan_path}...')
        if plan_type == Testplan.Type.PIPELINE:
            pass
        elif plan_type == Testplan.Type.TIMELINE:
            with open(plan_path, encoding='utf-8') as stream:
                plan_config = yaml.load(stream, yaml.FullLoader)
                self.plan = Timeline(plan_config)

    def setup_collector(self):
        logger.info('Raven is setting up statistics collector...')
        self.collector = Collector()

    def _execute_pipeline(self, plan: Pipeline):
        # database = workload['Database']
        # for query in workload['Queries']:
        #     self.engine.execute_query(database, query['SQL'])
        pass

    def _handle_stage(self, stage):
        pass

    def _execute_timeline(self, timeline: Timeline):
        logger.info(f'Raven is executing timeline: {timeline.name}...')
        # 给 Workload 中的每个事件设置一个定时器
        # 定时器触发时调用相应事件的 hook 处理事件
        threads = [Timer(event.time, self._handle_event, args=(event,)) for event in timeline.events]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        logger.info(f'Raven has finished executing timeline: {timeline.name}.')

    def _handle_event(self, event: Event):
        """
        根据事件名称调用相应的 hook 进行处理.
        :param event:
        :return:
        """
        logger.info(f'Raven is handling event: {event.name}...')
        hook = HookManager.get_hook(event.name)
        self._hook_exec_pool.submit(hook, self.engine)

        # 查询开始
        # 查询分为三个阶段: 查询生成, 查询执行, 收集指标
        # Generate -> Execute -> Collect
        if event.name == Event.Name.ON_QUERY_START:
            # 查询用例采用生产者消费者模式
            # workload 是生产者, engine 是消费者
            # 生产者和消费者之间通过查询请求队列进行通信

            # workload 启动若干个线程并发生成查询请求并放入请求队列中
            execute_queue = queue.Queue(maxsize=3000)
            collect_queue = queue.Queue(maxsize=3000)

            generate_thread = threading.Thread(
                target=self.workload.generate_queries,
                args=(execute_queue,),
                kwargs=self.config['Workload']['Parameters'],
                name='QueryGenerator'
            )
            generate_thread.start()

            # engine 启动若干个线程用于并发处理查询请求
            execute_thread = threading.Thread(
                target=self.engine.execute_queries,
                args=(execute_queue, collect_queue),
                name='QueryExecutor'
            )
            execute_thread.start()

            # metric collector 启动若干个线程去收集性能指标
            # 成本指标和资源利用率指标通过 AWS CloudWatch 去收集
            collect_thread = threading.Thread(
                target=self.collector.collect_queries,
                args=(collect_queue,),
                name='QueryCollector'
            )
            collect_thread.start()

            generate_thread.join()

            execute_queue.join()
            self.engine.cancel_execute()
            execute_thread.join()
            self.engine.shutdown()

            collect_queue.join()
            self.collector.cancel_collect()
            collect_thread.join()

            logger.info(f'Raven has finished handling event: {event.name}...')


if __name__ == '__main__':
    # Raven
    with open(os.path.join(os.environ['RAVEN_HOME'], 'config', 'raven.yaml'), encoding='utf-8') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
    raven = Raven(config)

    # Setup engine
    raven.setup_engine(engine_name=config['Engine']['Name'], **config['Engine']['Properties'])

    # Setup workload
    raven.setup_workload(workload_name=config['Workload']['Name'], workload_type=config['Workload']['Type'],
                         **config['Workload']['Parameters'])

    # Setup testplan
    raven.setup_testplan(plan_type=config['Testplan']['Properties']['Type'],
                         plan_path=os.path.join(os.environ['RAVEN_HOME'],
                                                *config['Testplan']['Properties']['Path'].split('/')))

    # Setup statistics collector
    raven.setup_collector()

    start = datetime.now()
    raven.run()
    end = datetime.now()

    raven.collector.generate_report(start=start, end=end)
