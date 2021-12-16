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
import math
import numbers
import os
import queue
import random
import threading
import time
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import configs
from benchmark.core.query import Query, Status

logger = configs.GENERATE_LOGGER


class Workload:
    class Distribution:
        """查询分布类型"""
        RANDOM: str = 'random'
        UNIFORM: str = 'uniform'
        POISSON: str = 'poisson'
        UNIMODAL: str = 'unimodal'
        BIMODAL: str = 'bimodal'
        INCREASE: str = 'increase'
        SURGE: str = 'surge'
        SUDDEN_SHRINK: str = 'sudden_shrink'

    def __init__(self, config: dict):
        """
        Name:
        Description:
        Database:
          Name:
          Create:
        Tables:
          TableID:
            Name:
            Create:
            Load
        Queries:
          QueryID:
            Name:
            SQL:
        :param config:
        """
        self.config = config
        self.name = config.get('Name', '')
        self.description = config.get('Description', '')
        self.database = config['Database']
        self.tables = config['Tables']
        self.total_queries = len(self.config['Queries'])
        self._current_queries: int = 0
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
        self._qps = 1.0
        self._generate_switch = False

    @property
    def qps(self):
        return self._qps

    @qps.setter
    def qps(self, value):
        if not isinstance(value, numbers.Number):
            raise TypeError(f'QPS must be a number.')
        elif value < 0:
            raise ValueError(f'QPS must be positive.')
        self._qps = value

    def __str__(self):
        return f'Workload(name={self.name},description="{self.description}")'

    def get_query_by_id(self, query_id: str) -> Query:
        query_config = self.config['Queries'][query_id]
        return Query(database=self.config['Database']['Name'], sql=query_config['SQL'], name=query_config['Name'])

    def get_random_query(self) -> Query:
        query_id = f'Q{random.randint(1, self.total_queries)}'
        return self.get_query_by_id(query_id)

    def generate_queries(self, execute_queue: queue.Queue, *, distribution: str = Distribution.UNIFORM,
                         duration: float = 3600.0, max_queries: Optional[int] = None,
                         collect_data: bool = True, **kwargs):
        """不断生成随机查询并放入查询请求队列中.
        :param collect_data:
        :param execute_queue: 查询请求队列
        :param distribution: 查询分布情况
        :param duration: 生成持续时间
        :param max_queries: 最大查询数, 如果设置该参数, 则将会在生成的查询数量超过该阈值后停止生成查询
        :param collect_data:
        :return filename of workload qps data
        """
        logger.info(f'Workload is generating queries with {distribution} distribution...')
        distribution = distribution.lower()
        self._generate_switch = True
        self._current_queries = 0
        self._start_time = time.time()
        self._end_time = self._start_time + duration
        if collect_data:
            threading.Thread(
                target=self._collect_data,
                name='WorkloadDataCollector'
            ).start()

        while self._generate_switch:
            if self._end_time and time.time() >= self._end_time:
                self._generate_switch = False
                logger.info(f'Workload has stopped generating queries: time of duration has exceeded {duration}.')
                logger.info(f'Workload duration: {time.time() - self._start_time:.3f}s.')
                logger.info(f'Number of queries generated: {self._current_queries}.')
                break
            if max_queries and self._current_queries >= max_queries:
                self._generate_switch = False
                logger.info(f'Workload has stopped generating queries: number of queries has exceeded {max_queries}.')
                logger.info(f'Workload duration: {time.time() - self._start_time:.3f}s.')
                logger.info(f'Number of queries generated: {self._current_queries}.')
                break
            self._update_qps(distribution, duration=duration, **kwargs)
            if self.qps < 0.1:
                time.sleep(0.01)
                continue
            time.sleep(1.0 / self.qps)
            query = self.get_random_query()
            logger.info(f'Workload has generated query: {query}.')
            query.set_status(Status.WAIT)
            execute_queue.put(query)
            self._current_queries += 1

    def generate_all_queries(self, execute_queue: queue.Queue, *, passes: int = 1, **kwargs):
        self._current_queries = 0
        self._start_time = time.time()
        for i in range(1, passes + 1):
            logger.info(f'Workload is generating all queries, pass {i} of {passes}...')
            for j in range(1, self.total_queries + 1):
                query_id = f'Q{j}'
                query = self.get_query_by_id(query_id)
                logger.info(f'Workload has generated query: {query}.')
                query.set_status(Status.WAIT)
                execute_queue.put(query, block=True)
                self._current_queries += 1

    def cancel_generate_queries(self):
        logger.info(f'Workload has canceled generating queries.')
        self._generate_switch = False
        logger.info(f'Workload duration: {time.time() - self._start_time:.3f}s.')
        logger.info(f'Number of queries generated: {self._current_queries}.')
        logger.info(f'Workload has finished generating queries.')

    def _collect_data(self, output_dir: str = None, filename: str = None):
        logger.info('Workload is collecting data about qps and number of queries generated...')
        df = pd.DataFrame(columns=('time', 'qps', 'queries'))
        while self._generate_switch:
            df = df.append({'time': time.time() - self._start_time, 'qps': self.qps, 'queries': self._current_queries},
                           ignore_index=True)
            time.sleep(1)
        if not output_dir:
            output_dir = os.path.join(os.environ['RAVEN_HOME'], 'out', 'workloads',
                                      f'workload_{time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())}')
        os.makedirs(output_dir, exist_ok=True)
        if not filename:
            filename = 'workload.csv'
        df.to_csv(os.path.join(output_dir, filename), encoding='utf-8')
        logger.info('Workload has finished collecting data...')

        # visualize qps and queries
        Workload.visualize(df, output_dir=output_dir)

    def _update_qps(self, distribution, **kwargs):
        """根据查询分布情况不断更新 QPS"""
        if distribution == Workload.Distribution.RANDOM:
            self._update_qps_with_uniform_distribution(**kwargs)
        elif distribution == Workload.Distribution.UNIFORM:
            self._update_qps_with_uniform_distribution(**kwargs)
        elif distribution == Workload.Distribution.POISSON:
            self._update_qps_with_poisson_distribution(**kwargs)
        elif distribution == Workload.Distribution.UNIMODAL:
            self._update_qps_with_unimodal_distribution(**kwargs)
        elif distribution == Workload.Distribution.BIMODAL:
            self._update_qps_with_bimodal_distribution(**kwargs)
        elif distribution == Workload.Distribution.INCREASE:
            self._update_qps_with_increase_distribution(**kwargs)
        elif distribution == Workload.Distribution.SURGE:
            self._update_qps_with_surge_distribution(**kwargs)
        elif distribution == Workload.Distribution.SUDDEN_SHRINK:
            self._update_qps_with_sudden_shrink_distribution(**kwargs)
        else:
            raise ValueError('Not supported distribution type.')

    def _update_qps_with_uniform_distribution(self, *, duration: float = 60.0, qps: float = 1.0):
        self.qps = qps

    def _update_qps_with_poisson_distribution(self, *, duration: float = 60.0, lam: float = 5.0):
        """按照泊松分布更新 QPS.
        :param lam: 泊松分布的 lambda 参数
        """
        interval = np.random.exponential(scale=1 / lam)
        self.qps = 1 / interval

    def _update_qps_with_unimodal_distribution(self, *, duration: float = 60.0, max_qps: float = 100.0):
        """按照单峰分布更新 QPS.
        :param duration: 单峰分布总持续时间
        :param max_qps
        """
        current_time = time.time() - self._start_time

        a, t0, t = max_qps, duration, current_time
        b = 4 * math.log(a) / math.pow(t0, 2)
        self.qps = a * math.exp(-1 * b * (t - t0 / 2) ** 2)

    def _update_qps_with_bimodal_distribution(self, *, duration: float = 60.0, max_qps: float = 100.0):
        current_time = time.time() - self._start_time

        a, t0, t = max_qps, duration, current_time
        b = 16 * math.log(a) / (t0 ** 2)
        if t < t0 / 2:
            self.qps = a * math.exp(-1 * b * (t - t0 / 4) ** 2)
        else:
            self.qps = a * math.exp(-1 * b * (t - t0 * 3 / 4) ** 2)

    def _update_qps_with_increase_distribution(self, *, duration: float = 60.0, max_qps: float = 100.0):
        k = max_qps / duration
        t = time.time() - self._start_time
        self.qps = k * t

    def _update_qps_with_surge_distribution(self, *, duration: float = 60.0, max_qps: float = 1000, surge_time: float = 20,
                                            end: float = 40):
        a, s, e = max_qps, surge_time, end
        b = 4 * math.log(a) / (e - s) ** 2
        t = time.time() - self._start_time
        if s <= t <= e:
            self.qps = a * math.exp(-1 * b * (t - (s + e) / 2) ** 2)
        else:
            self.qps = 0

    def _update_qps_with_sudden_shrink_distribution(self, *, duration: float = 60.0, max_qps: float = 100.0,
                                                    shrink_time: float = 50):
        a, t0, t1 = max_qps, duration, shrink_time
        k = a / t1
        b = math.log(a) / (t0 - t1) ** 2
        t = time.time() - self._start_time
        if t < t1:
            self.qps = k * t
        else:
            self.qps = a * math.exp(-1 * b * (t - t1) ** 2)

    @staticmethod
    def visualize(df: pd.DataFrame, output_dir: str = None):
        os.makedirs(output_dir, exist_ok=True)
        Workload.visualize_qps(df, output_dir=output_dir)
        Workload.visualize_queries(df, output_dir=output_dir)

    @staticmethod
    def visualize_qps(df: pd.DataFrame, output_dir: str = None):
        logger.info('Workload is visualizing qps.')
        x = df['time']
        y = df['qps']
        plt.plot(x, y)
        plt.xlabel('Time')
        plt.ylabel('QPS')
        if output_dir:
            plt.savefig(fname=os.path.join(output_dir, 'qps'))
        # plt.show()

    @staticmethod
    def visualize_queries(df: pd.DataFrame, output_dir: str = None):
        logger.info('Workload is visualizing queries.')
        x = df['time']
        y = df['queries']
        plt.plot(x, y)
        plt.xlabel('Time')
        plt.ylabel('Queries')
        if output_dir:
            plt.savefig(fname=os.path.join(output_dir, 'queries'))
        # plt.show()

    @staticmethod
    def visualization_alive(path: str):
        df = pd.read_csv(path, index_col=0)
        dirname = os.path.dirname(path)
        filename = os.path.join(dirname, os.path.basename(path).split('.')[0] + '.git')
        df.fillna(0).plot_animated(filename=filename)
