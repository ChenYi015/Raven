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

import abc
import copy
import math
import numbers
import random
import time
from datetime import datetime
from queue import Queue
from typing import List, Optional

import numpy as np

import configs
from benchmark.core.query import Query, QueryStatus

logger = configs.GENERATE_LOGGER


class Workload(metaclass=abc.ABCMeta):
    """Abstract workload."""

    def __init__(self, *, name: str, description: str = '', queries: List[Query] = None):
        """

        :param name: The workload name.
        :param description: The workload description.
        :param queries: All queries that comprise the workload.
        """

        self.name = name
        self.description = description
        self.queries = queries if queries else []

    def __str__(self):
        return f"Workload(name='{self.name}', description='{self.description}')"

    def append_query(self, query: Query):
        """Append query to the workload."""
        self.queries.append(query)

    def set_database(self, database: str):
        for query in self.queries:
            query.database = database

    def get_random_query(self) -> Query:
        """Get random query from the workload.

        :return: Random query selected from the workload
        """
        n = len(self.queries)
        random_index = random.randint(0, n - 1)
        return copy.copy(self.queries[random_index])

    @abc.abstractmethod
    def generate_queries(self, queue: Queue, **kwargs):
        pass


class LoopWorkload(Workload):
    """Workload which can generate multiple loops of queries."""

    def __init__(self, *, name: str, description: str = '', queries: List[Query] = None):
        super().__init__(name=name, description=description, queries=queries)

    def generate_queries(self, queue: Queue, **kwargs):
        self.generate_multiple_loop_queries(queue, loops=kwargs.get('loops', 1))

    def generate_one_loop_queries(self, queue: Queue):
        """The workload generate all queries with one loop.

        :param queue: The queue to put generated queries.
        :return:
        """
        n = len(self.queries)
        for i in range(n):
            query = copy.copy(self.queries[i])
            queue.put(query)
            query.status = QueryStatus.QUEUED
            logger.info(f'{self} has generated {query}.')

    def generate_multiple_loop_queries(self, queue: Queue, *, loops: int = 1):
        """The workload generate multiple loops of queries.

        :param queue:
        :param loops:
        :return:
        """
        for i in range(loops):
            self.generate_one_loop_queries(queue)


class QpsWorkload(Workload):
    """Workload which qps varies with diverse distributions as time goes on."""

    class Distribution:
        """查询分布类型"""
        RANDOM: str = 'RANDOM'
        UNIFORM: str = 'UNIFORM'
        POISSON: str = 'POISSON'
        UNIMODAL: str = 'UNIMODAL'
        BIMODAL: str = 'BIMODAL'
        INCREASE: str = 'INCREASE'
        SURGE: str = 'SURGE'
        SUDDEN_SHRINK: str = 'SUDDEN_SHRINK'

    def __init__(self, *, name: str, description: str = '', queries: List[Query] = None):
        super().__init__(name=name, description=description, queries=queries)
        self._qps: float = 1.0
        self._generate_switch: bool = False

        self._current_queries: int = 0
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None

    @property
    def qps(self) -> float:
        return self._qps

    @qps.setter
    def qps(self, value):
        if not isinstance(value, numbers.Number):
            raise TypeError(f'QPS must be a number.')
        elif value < 0:
            raise ValueError(f'QPS must be positive.')
        self._qps = value

    def generate_queries(self, queue: Queue, **kwargs):
        self.generate_queries_with_distribution(queue, **kwargs)

    def get_random_query(self) -> Query:
        """Get random query from the workload.

        :return: Random query selected from the workload
        """
        n = len(self.queries)
        random_index = random.randint(0, n - 1)
        return copy.copy(self.queries[random_index])

    def generate_queries_with_distribution(self, queue: Queue, *, distribution: str, duration: float = 60.0,
                                           max_queries: int = 10000, **kwargs):
        """Generate queries that satisfy the specified distribution.

        :param queue:
        :param distribution:
        :param duration:
        :param max_queries:
        :param kwargs:
        :return:
        """
        logger.info(f'Workload is generating queries with {distribution} distribution...')
        self._generate_switch = True
        self._current_queries = 0
        self._start_time = time.time()
        self._end_time = self._start_time + duration

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
            query.status = QueryStatus.QUEUED
            queue.put(query)
            self._current_queries += 1

    def cancel_generate_queries(self):
        logger.info(f'Workload has canceled generating queries.')
        self._generate_switch = False
        logger.info(f'Workload duration: {time.time() - self._start_time:.3f}s.')
        logger.info(f'Number of queries generated: {self._current_queries}.')
        logger.info(f'Workload has finished generating queries.')

    def _update_qps(self, distribution, **kwargs):
        distribution = distribution.upper()
        """根据查询分布情况不断更新 QPS"""
        if distribution == QpsWorkload.Distribution.RANDOM:
            self._update_qps_with_uniform_distribution(**kwargs)
        elif distribution == QpsWorkload.Distribution.UNIFORM:
            self._update_qps_with_uniform_distribution(**kwargs)
        elif distribution == QpsWorkload.Distribution.POISSON:
            self._update_qps_with_poisson_distribution(**kwargs)
        elif distribution == QpsWorkload.Distribution.UNIMODAL:
            self._update_qps_with_unimodal_distribution(**kwargs)
        elif distribution == QpsWorkload.Distribution.BIMODAL:
            self._update_qps_with_bimodal_distribution(**kwargs)
        elif distribution == QpsWorkload.Distribution.INCREASE:
            self._update_qps_with_increase_distribution(**kwargs)
        elif distribution == QpsWorkload.Distribution.SURGE:
            self._update_qps_with_surge_distribution(**kwargs)
        elif distribution == QpsWorkload.Distribution.SUDDEN_SHRINK:
            self._update_qps_with_sudden_shrink_distribution(**kwargs)
        else:
            raise ValueError(f'Not supported distribution type: {distribution}.')

    def _update_qps_with_uniform_distribution(self, *, duration: float = 60.0, qps: float = 1.0, **kwargs):
        self.qps = qps

    def _update_qps_with_poisson_distribution(self, *, duration: float = 60.0, lam: float = 5.0, **kwargs):
        """按照泊松分布更新 QPS.
        :param lam: 泊松分布的 lambda 参数
        """
        interval = np.random.exponential(scale=1 / lam)
        self.qps = 1 / interval

    def _update_qps_with_unimodal_distribution(self, *, duration: float = 60.0, max_qps: float = 100.0, **kwargs):
        """按照单峰分布更新 QPS.
        :param duration: 单峰分布总持续时间
        :param max_qps
        """
        current_time = time.time() - self._start_time

        a, t0, t = max_qps, duration, current_time
        b = 4 * math.log(a) / math.pow(t0, 2)
        self.qps = a * math.exp(-1 * b * (t - t0 / 2) ** 2)

    def _update_qps_with_bimodal_distribution(self, *, duration: float = 60.0, max_qps: float = 100.0, **kwargs):
        current_time = time.time() - self._start_time

        a, t0, t = max_qps, duration, current_time
        b = 16 * math.log(a) / (t0 ** 2)
        if t < t0 / 2:
            self.qps = a * math.exp(-1 * b * (t - t0 / 4) ** 2)
        else:
            self.qps = a * math.exp(-1 * b * (t - t0 * 3 / 4) ** 2)

    def _update_qps_with_increase_distribution(self, *, duration: float = 60.0, max_qps: float = 100.0, **kwargs):
        k = max_qps / duration
        t = time.time() - self._start_time
        self.qps = k * t

    def _update_qps_with_surge_distribution(self, *, duration: float = 60.0, max_qps: float = 1000,
                                            surge_time: float = 20, end: float = 40, **kwargs):
        a, s, e = max_qps, surge_time, end
        b = 4 * math.log(a) / (e - s) ** 2
        t = time.time() - self._start_time
        if s <= t <= e:
            self.qps = a * math.exp(-1 * b * (t - (s + e) / 2) ** 2)
        else:
            self.qps = 0

    def _update_qps_with_sudden_shrink_distribution(self, *, duration: float = 60.0, max_qps: float = 100.0,
                                                    shrink_time: float = 50, **kwargs):
        a, t0, t1 = max_qps, duration, shrink_time
        k = a / t1
        b = math.log(a) / (t0 - t1) ** 2
        t = time.time() - self._start_time
        if t < t1:
            self.qps = k * t
        else:
            self.qps = a * math.exp(-1 * b * (t - t1) ** 2)


class TimelineWorkload(Workload):

    def __init__(self, *, name: str, description: str = '', queries: List[Query] = None, timeline: List[datetime]):
        super().__init__(name=name, description=description, queries=queries)
        self._timeline = [t.timestamp() for t in timeline]
        self._timeline.sort()

    def generate_queries(self, queue: Queue, **kwargs):
        prev = self._timeline[0]
        for t in self._timeline:
            time.sleep(t - prev)
            query = self.get_random_query()
            query.status = QueryStatus.QUEUED
            queue.put(query)
            prev = t
            logger.info(f'{self} has generated {query}.')
