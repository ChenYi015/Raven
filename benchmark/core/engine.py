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
from concurrent.futures._base import Future
from concurrent.futures.thread import ThreadPoolExecutor
import queue

import configs
from benchmark.core.query import Query

logger = configs.EXECUTE_LOGGER


class Engine(metaclass=abc.ABCMeta):

    def __init__(self, name: str, description: str, concurrency: int = 1):
        self.name = name
        self.description = description
        self.concurrency = concurrency
        self._execute_switch = False
        self._execute_thread_pool = ThreadPoolExecutor(
            max_workers=self.concurrency,
            thread_name_prefix='QueryExecutor'
        )

    def launch(self):
        logger.info(f'{self.name} is launching...')
        logger.info(f'{self.name} has launched.')

    @abc.abstractmethod
    def execute_query(self, query: Query) -> Query:
        pass

    def shutdown(self):
        logger.info(f'{self.name} is shutting down...')
        logger.info(f'{self.name} has shut down. ')

    def execute_queries(self, execute_queue: queue.Queue, collect_queue: queue.Queue):
        """OLAP engine will get queries from one queue and put queries which have been processed into another queue.

        :param execute_queue: OLAP engine will get queries from this queue.
        :param collect_queue: Queries which have already been processed will put into this queue.
        :return:
        """

        def execute_callback(_future: Future):
            execute_queue.task_done()
            collect_queue.put(_future.result())

        logger.info(f'{self.name} is executing queries...')
        self._execute_switch = True
        while self._execute_switch:
            try:
                query = execute_queue.get(block=True, timeout=1)
            except queue.Empty:
                continue
            try:
                future = self._execute_thread_pool.submit(self.execute_query, query)
                future.add_done_callback(execute_callback)
            except TimeoutError as error:
                logger.error(
                    f'{self.name} engines failed to execute_queries query: {query}, an error has occurred: {error}')

    def cancel_execute(self):
        """Cancel executing queries."""
        logger.info(f'{self.name} engine has canceled executing queries.')
        self._execute_switch = False
        self._execute_thread_pool.shutdown(wait=True)
        logger.info(f'{self.name} engine has finished executing queries.')
