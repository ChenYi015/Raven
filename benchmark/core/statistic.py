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

import os
import time
import queue
from typing import List

import numpy as np
import pandas as pd
from jinja2 import Environment, PackageLoader, select_autoescape, Template

import configs
from benchmark.core.query import Query, Status

logger = configs.COLLECT_LOGGER


class Metric:
    """指标相关的字符串常量."""

    # Queries
    TOTAL_QUERIES = 'TOTAL_QUERIES'
    TOTAL_SUCCEEDED_QUERIES = 'TOTAL_SUCCEEDED_QUERIES'
    TOTAL_FAILED_QUERIES = 'TOTAL_FAILED_QUERIES'

    # TotalTime
    START_TIME = 'START_TIME'
    END_TIME = 'END_TIME'
    TOTAL_ELAPSED_TIME = 'TOTAL_ELAPSED_TIME'

    # ReactionTime
    REACTION_TIME = 'REACTION_TIME'
    AVERAGE_REACTION_TIME = 'AVERAGE_REACTION_TIME'
    MEDIAN_REACTION_TIME = 'MEDIAN_REACTION_TIME'
    MIN_REACTION_TIME = 'MIN_REACTION_TIME'
    MAX_REACTION_TIME = 'MAX_REACTION_TIME'
    PERCENTILE_REACTION_TIME = 'PERCENTILE_REACTION_TIME'

    # Latency
    LATENCY = 'LATENCY'
    AVERAGE_LATENCY = 'AVERAGE_LATENCY'
    MEDIAN_LATENCY = 'MEDIAN_LATENCY'
    MIN_LATENCY = 'MIN_LATENCY'
    MAX_LATENCY = 'MAX_LATENCY'
    PERCENTILE_LATENCY = 'PERCENTILE_LATENCY'

    # ResponseTime
    RESPONSE_TIME = 'RESPONSE_TIME'
    AVERAGE_RESPONSE_TIME = 'AVERAGE_RESPONSE_TIME'
    MEDIAN_RESPONSE_TIME = 'MEDIAN_RESPONSE_TIME'
    MIN_RESPONSE_TIME = 'MIN_RESPONSE_TIME'
    PERCENTILE_RESPONSE_TIME = 'PERCENTILE_RESPONSE_TIME'
    MAX_RESPONSE_TIME = 'MAX_RESPONSE_TIME'

    # Cost
    TOTAL_COST = 'TOTAL_COST'
    PRE_COMPUTING_COST = 'PRE_COMPUTING_COST'
    QUERY_COST = 'QUERY_COST'

    # CPU Utilization
    AVERAGE_CPU_UTILIZATION = 'AVERAGE_CPU_UTILIZATION'

    # Memory Utilization
    AVERAGE_MEMORY_UTILIZATION = 'AVERAGE_MEMORY_UTILIZATION'

    # Disk Utilization
    AVERAGE_DISK_UTILIZATION = 'AVERAGE_DISK_UTILIZATION'


class Collector:

    def __init__(self):
        self.data: pd.DataFrame = pd.DataFrame(
            columns=['Name', 'Description', 'Database', 'Sql', 'FinalStatus', 'WaitStart', 'WaitFinish', 'ExecuteStart',
                     'ExecuteFinish']
        )
        self._collect_switch = False

    def collect_queries(self, collect_queue: queue.Queue):
        logger.info('Statistics collector is collecting query metrics...')
        self._collect_switch = True
        while self._collect_switch:
            try:
                query = collect_queue.get(block=True, timeout=1)
                self.collect_query(query)
                collect_queue.task_done()
            except queue.Empty:
                pass

    def collect_query(self, query: Query):
        logger.info(f'Statistics collector is collecting query: {query}')
        self.data = self.data.append(query.get_metrics(), ignore_index=True)
        logger.info(f'Statistics collector has finished collecting query: {query}')

    def cancel_collect(self):
        """Cancel collecting queries."""
        logger.info('Statistics collector has canceled collecting query metrics.')
        self._collect_switch = False
        logger.info('Statistics collector has finished collecting query metrics.')

    def _calculate_metrics(self) -> dict:
        logger.info('Statistics collector is calculating metrics...')
        metrics = {}

        self.data[Metric.REACTION_TIME] = self.data['WaitFinish'] - self.data['WaitStart']
        self.data[Metric.LATENCY] = self.data['ExecuteFinish'] - self.data['ExecuteStart']
        self.data[Metric.RESPONSE_TIME] = self.data['ExecuteFinish'] - self.data['WaitStart']
        succeeded_queries: pd.DataFrame = self.data[self.data['FinalStatus'] == Status.SUCCEEDED]
        failed_queries: pd.DataFrame = self.data[self.data['FinalStatus'] == Status.FAILED]

        metrics[Metric.TOTAL_QUERIES] = len(self.data)
        metrics[Metric.TOTAL_SUCCEEDED_QUERIES] = len(succeeded_queries)
        metrics[Metric.TOTAL_FAILED_QUERIES] = len(failed_queries)

        metrics[Metric.AVERAGE_REACTION_TIME] = np.mean(succeeded_queries[Metric.REACTION_TIME])
        metrics[Metric.MEDIAN_RESPONSE_TIME] = np.median(succeeded_queries[Metric.REACTION_TIME])
        metrics[Metric.MIN_REACTION_TIME] = np.min(succeeded_queries[Metric.REACTION_TIME])
        metrics[Metric.MAX_REACTION_TIME] = np.max(succeeded_queries[Metric.REACTION_TIME])
        metrics[Metric.PERCENTILE_REACTION_TIME] = np.percentile(succeeded_queries[Metric.REACTION_TIME], 95)

        metrics[Metric.AVERAGE_LATENCY] = np.mean(succeeded_queries[Metric.LATENCY])
        metrics[Metric.MEDIAN_LATENCY] = np.median(succeeded_queries[Metric.LATENCY])
        metrics[Metric.MIN_LATENCY] = np.min(succeeded_queries[Metric.LATENCY])
        metrics[Metric.MAX_LATENCY] = np.max(succeeded_queries[Metric.LATENCY])
        metrics[Metric.PERCENTILE_LATENCY] = np.percentile(succeeded_queries[Metric.LATENCY], 95)

        metrics[Metric.AVERAGE_RESPONSE_TIME] = np.mean(succeeded_queries[Metric.RESPONSE_TIME])
        metrics[Metric.MEDIAN_RESPONSE_TIME] = np.median(succeeded_queries[Metric.RESPONSE_TIME])
        metrics[Metric.MIN_RESPONSE_TIME] = np.min(succeeded_queries[Metric.RESPONSE_TIME])
        metrics[Metric.MAX_RESPONSE_TIME] = np.max(succeeded_queries[Metric.RESPONSE_TIME])
        metrics[Metric.PERCENTILE_RESPONSE_TIME] = np.percentile(succeeded_queries[Metric.RESPONSE_TIME], 95)

        logger.info('Statistics collector has finished calculating metrics.')
        return metrics

    def generate_report(self, template: Template = None, filename: str = None, **kwargs):
        """生成基准测试报告.

        生成的报告存放在 reports 目录下.

        :param template: 报告 jinja2 模板
        :param filename: 报告文件名
        """
        logger.info('Statistics collector is rendering report...')
        metrics = self._calculate_metrics()

        # Setup template
        env = Environment(
            loader=PackageLoader('report', 'template'),
            autoescape=select_autoescape()
        )
        if template is None:
            template = env.get_template('report.jinja2')

        now = time.localtime()

        if filename is None:
            filename = 'report_{}.txt'.format(time.strftime('%Y-%m-%d_%H-%M-%S', now))

        # Rendering template
        metrics[Metric.START_TIME] = kwargs['start'].strftime('%Y-%m-%d %H:%M:%S')
        metrics[Metric.END_TIME] = kwargs['end'].strftime('%Y-%m-%d %H:%M:%S')

        output_dir = os.path.join(os.environ['RAVEN_HOME'], 'report')
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        with open(filepath, mode='w', encoding='utf-8') as out:
            out.write(template.render(metrics))

        with open(filepath, encoding='utf-8') as report:
            for line in report.readlines():
                print(line, end='')

        logger.info('Statistics collector has finished rendering report.')
        logger.info(f'Path of report: {filepath}')

    def clear(self):
        self.data.drop(index=pd.RangeIndex(0, len(self.data)), inplace=True)
