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
from concurrent.futures.thread import ThreadPoolExecutor

from benchmark.core.query import Query


class AbstractEngine(metaclass=abc.ABCMeta):

    def __init__(self, config: dict):
        self.name = config['Name']
        self.description = config['Description']
        self.concurrency = config['Properties']['Concurrency']
        self._query_exec_pool = ThreadPoolExecutor(max_workers=self.concurrency)

    @abc.abstractmethod
    def launch(self):
        pass

    def execute_queries(self, query_queue: queue.Queue):
        while True:
            query = query_queue.get()
            self._query_exec_pool.submit(self.execute_query, query)

    @abc.abstractmethod
    def execute_query(self, query: Query):
        pass

    @abc.abstractmethod
    def shutdown(self):
        pass
