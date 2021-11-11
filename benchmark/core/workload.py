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

import queue
import random
import time
from queue import Queue
from enum import Enum

from benchmark.core.query import Query


class Workload:

    def __init__(self, config: dict):
        self.config = config
        self.name = config['Name']
        self.description = config['Description'] if 'Description' in config else ''
        self.database = config['Database']
        self.tables = config['Tables']

    def get_query_by_id(self, query_id: str):
        config = self.config['Queries'][query_id]
        return Query(database=self.config['Database']['Name'], sql=config['SQL'], name=config['Name'])

    def generate_random_queries(self, query_queue: queue.Queue):
        while True:
            time.sleep(random.randint(1, 3))
            n = len(self.config['Queries'])
            query = self.get_query_by_id(f'Q{random.randint(1, n)}')
            query.wait_start = time.time()
            query_queue.put(query)

    def __str__(self):
        return f'Workload {self.name}: {self.description}'
