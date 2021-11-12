# Copyright 2021 Statistics collector Authors. All rights reserved.
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
import time
from concurrent.futures.thread import ThreadPoolExecutor
import queue
from typing import List

import numpy as np
import yaml
from jinja2 import Environment, PackageLoader, select_autoescape, Template

from benchmark.core.metric import Metric
from benchmark.core.query import Query, Status


class Collector:

    def __init__(self):
        self.total_queries: int = 0
        self.total_finish_queries: int = 0
        self.total_fail_queries: int = 0

        self.metrics: dict = {}
        self.query_metrics: List[dict] = []

        self.start = None
        self.end = None

        self._concurrency = 1
        self._collect_thread_pool = ThreadPoolExecutor(
            max_workers=self.concurrency,
            thread_name_prefix='CollectWorker'
        )
        self._collect_switch = False

    @property
    def concurrency(self):
        return self._concurrency

    @concurrency.setter
    def concurrency(self, value):
        if not isinstance(value, int):
            raise TypeError(f'Concurrency must be integer.')
        elif value <= 0:
            raise ValueError(f'Concurrency must be positive.')
        self._concurrency = value

    def collect(self, collect_queue: queue.Queue):
        logging.info('Statistics collector is collecting queries...')
        self.start = time.time()
        self._collect_switch = True
        for i in range(self.concurrency):
            self._collect_thread_pool.submit(self.collect_queries, collect_queue)

    def collect_queries(self, collect_queue: queue.Queue):
        while self._collect_switch:
            try:
                query = collect_queue.get(block=True, timeout=1)
                self.collect_query(query)
                collect_queue.task_done()
            except queue.Empty:
                pass

    def cancel_collect(self):
        """Cancel collecting queries."""
        logging.info('Statistics collector has canceled collecting queries.')
        self._collect_switch = False
        self._collect_thread_pool.shutdown(wait=True)
        self.end = time.time()
        self.metrics[Metric.TOTAL_ELAPSED_TIME] = self.end - self.start
        logging.info('Statistics collector has finished collecting queries.')

    def collect_query(self, query: Query):
        # logging.info(f'Statistics collector is collecting query: {query}')
        self.query_metrics.append(query.get_metric_dict())
        self.total_finish_queries += 1
        if query.status == Status.FINISH:
            self.total_finish_queries += 1
        elif query.status == Status.FAIL:
            self.total_fail_queries += 1
        logging.info(f'Statistics collector has finished collecting query: {query}')

    def _calculate_metrics(self):
        logging.info('Statistics collector is calculating metrics...')
        # 计算执行成功的查询的各种指标
        succeed_query_metrics = list(filter(lambda x: x['status'] == Status.FINISH, self.query_metrics))
        try:
            reaction_times = [metric_dict[Metric.REACTION_TIME] for metric_dict in succeed_query_metrics]
            self.metrics[Metric.AVERAGE_REACTION_TIME] = np.mean(reaction_times)
            self.metrics[Metric.MEDIAN_RESPONSE_TIME] = np.median(reaction_times)
            self.metrics[Metric.MIN_REACTION_TIME] = np.min(reaction_times)
            self.metrics[Metric.MAX_REACTION_TIME] = np.max(reaction_times)
            self.metrics[Metric.PERCENTILE_REACTION_TIME] = np.percentile(reaction_times, 95)

            response_times = [metric_dict[Metric.RESPONSE_TIME] for metric_dict in succeed_query_metrics]
            self.metrics[Metric.AVERAGE_RESPONSE_TIME] = np.mean(response_times)
            self.metrics[Metric.MEDIAN_RESPONSE_TIME] = np.median(response_times)
            self.metrics[Metric.MIN_RESPONSE_TIME] = np.min(response_times)
            self.metrics[Metric.MAX_RESPONSE_TIME] = np.max(response_times)
            self.metrics[Metric.PERCENTILE_RESPONSE_TIME] = np.percentile(response_times, 95)

            latencies = [metric_dict[Metric.LATENCY] for metric_dict in succeed_query_metrics]
            self.metrics[Metric.AVERAGE_LATENCY] = np.mean(latencies)
            self.metrics[Metric.MEDIAN_LATENCY] = np.median(latencies)
            self.metrics[Metric.MIN_LATENCY] = np.min(latencies)
            self.metrics[Metric.MAX_LATENCY] = np.max(latencies)
            self.metrics[Metric.PERCENTILE_LATENCY] = np.percentile(latencies, 95)
            logging.info('Statistics collector has finished calculating metrics.')
        except ValueError as error:
            logging.error(f'Statistics collector failed to calculate metrics: {error}.')

    def generate_report(self, template: Template = None, filename: str = None):
        """生成基准测试报告.

        生成的报告存放在 reports 目录下.

        :param template: 报告 jinja2 模板
        :param filename: 报告文件名
        """
        logging.info('Statistics collector is rendering report...')
        self._calculate_metrics()

        # Setup template
        env = Environment(
            loader=PackageLoader('reports', 'templates'),
            autoescape=select_autoescape()
        )
        if template is None:
            template = env.get_template('report.jinja2')

        now = time.localtime()

        if filename is None:
            filename = 'report_{}.txt'.format(time.strftime('%Y-%m-%d_%H-%M-%S', now))

        # Rendering template
        self.metrics['date'] = time.strftime('%Y-%m-%d %H:%M:%S', now)

        path = os.path.join(os.environ['RAVEN_HOME'], 'reports', filename)
        with open(path, mode='w', encoding='utf-8') as out:
            out.write(template.render(self.metrics))

        with open(path, mode='r', encoding='utf-8') as report:
            for line in report.readlines():
                print(line)

        logging.info('Statistics collector has finished rendering report.')
        logging.info(f'Path of report: {path}')

    def clear(self):
        self.start = None
        self.end = None
        self.metrics = None
        self.query_metrics = None


if __name__ == '__main__':
    os.chdir(os.environ['RAVEN_HOME'])

    # Logging
    with open(os.path.join(os.environ['RAVEN_HOME'], 'configs', 'logging.yaml'), encoding='utf-8') as file:
        logging_config = yaml.load(file, Loader=yaml.FullLoader)
        logging.config.dictConfig(logging_config)

    collector = Collector()
    collector.generate_report()