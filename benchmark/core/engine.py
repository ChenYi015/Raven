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
import queue
from concurrent.futures import Future, wait, ALL_COMPLETED
from concurrent.futures.thread import ThreadPoolExecutor

import configs
from benchmark.core.query import Query

logger = configs.EXECUTE_LOGGER


class AbstractEngine(metaclass=abc.ABCMeta):

    def __init__(self, config: dict):
        self.name = config['Name']
        self.description = config['Description']
        self._concurrency = 1
        self.concurrency = config['Properties']['Concurrency']
        self._execute_thread_pool = ThreadPoolExecutor(
            max_workers=self.concurrency,
            thread_name_prefix='ExecuteWorker'
        )
        self._execute_switch = False

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

    @abc.abstractmethod
    def launch(self):
        pass

    @abc.abstractmethod
    def execute_query(self, query: Query) -> Query:
        pass

    @abc.abstractmethod
    def shutdown(self):
        pass

    def execute(self, execute_queue: queue.Queue, collect_queue: queue.Queue):
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
                logger.error(f'{self.name} engines failed to execute query: {query}, an error has occurred: {error}')

    def execute_queries(self, execute_queue: queue.Queue, collect_queue: queue.Queue):
        while self._execute_switch:
            try:
                query = execute_queue.get(block=True, timeout=1)
                self.execute_query(query)
                execute_queue.task_done()
                collect_queue.put(query)
            except queue.Empty:
                pass

    def cancel_execute(self):
        """Cancel executing queries."""
        logger.info(f'{self.name} engine has canceled executing queries.')
        self._execute_switch = False
        self._execute_thread_pool.shutdown(wait=True)
        logger.info(f'{self.name} engine has finished executing queries.')
