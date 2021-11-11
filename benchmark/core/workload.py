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
import logging
import random
import time
from concurrent.futures._base import Future, as_completed
from concurrent.futures.thread import ThreadPoolExecutor
from queue import Queue
from typing import List

from benchmark.core.query import Query, Status


class Distribution:
    RANDOM = 'random'
    AVERAGE = 'average'
    BIMODAL = 'bimodal'
    INCREASE = 'increase'
    SHRINK = 'shrink'


class Workload:

    def __init__(self, config: dict):
        self.config = config
        self.name = config['Name']
        self.description = config['Description'] if 'Description' in config else ''
        self.database = config['Database']
        self.tables = config['Tables']
        self.total_queries = len(self.config['Queries'])

        self._concurrency = 3
        self._generate_thread_pool = ThreadPoolExecutor(
            max_workers=self.concurrency,
            thread_name_prefix='GenerateWorker'
        )
        self._generate_switch = False

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

    def get_query_by_id(self, query_id: str) -> Query:
        query_config = self.config['Queries'][query_id]
        return Query(database=self.config['Database']['Name'], sql=query_config['SQL'], name=query_config['Name'])

    def get_random_query(self) -> Query:
        query_id = f'Q{random.randint(1, self.total_queries)}'
        return self.get_query_by_id(query_id)

    def generate(self, execute_queue: Queue, distribution: str = 'random'):
        logging.info(f'Workload is generating queries with {distribution} distribution...')
        self._generate_switch = True
        futures: List[Future] = [self._generate_thread_pool.submit(self.generate_queries, execute_queue, distribution)
                                 for _ in
                                 range(self.concurrency)]
        # for i in range(len(futures)):
        #     future: Future = futures[i]
        #     future.exception()

    def cancel_generate(self):
        logging.info(f'Workload has canceled generating queries.')
        self._generate_switch = False
        self._generate_thread_pool.shutdown(wait=True)
        logging.info(f'Workload has finished generating queries.')

    def generate_queries(self, execute_queue: Queue, distribution: str = 'random'):
        """生成满足特定分布特征的查询请求

        :param execute_queue: 查询请求队列
        :param distribution 分布特征, 允许的值包括 random, average, bimodal, increase, shrink
        """
        if distribution == Distribution.RANDOM:
            self.generate_random_queries(execute_queue)
        elif distribution == Distribution.AVERAGE:
            self.generate_average_queries(execute_queue)
        elif distribution == Distribution.BIMODAL:
            self.generate_bimodal_queries(execute_queue)
        elif distribution == Distribution.INCREASE:
            self.generate_increase_queries(execute_queue)
        elif distribution == Distribution.SHRINK:
            self.generate_shrink_queries(execute_queue)
        else:
            raise ValueError('Not supported distribution type.')

    def generate_random_queries(self, execute_queue: Queue, interval=3):
        """随机生成查询请求.

        @:type int
        @:param interval: 查询请求间隔为 [0, interval].
        """
        while self._generate_switch:
            time.sleep(random.randint(1, interval))
            query = self.get_random_query()
            logging.info(f'Workload has generated query: {query}.')
            query.set_status(Status.WAIT)
            execute_queue.put(query)

    def generate_average_queries(self, query_queue: Queue):
        raise Exception('Not supported average distribution.')

    def generate_bimodal_queries(self, query_queue: Queue):
        raise Exception('Not supported bimodal distribution.')

    def generate_increase_queries(self, query_queue: Queue):
        raise Exception('Not supported increase distribution.')

    def generate_shrink_queries(self, query_queue: Queue):
        raise Exception('Not supported shrink distribution.')

    def __str__(self):
        return f'Workload {self.name}: {self.description}'
