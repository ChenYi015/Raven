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

from queue import Queue
from threading import Thread

from benchmark.core.workload import QpsWorkload
from benchmark.workload.ssb import SsbQpsWorkload


def print_queries(queue: Queue):
    while True:
        query = queue.get()
        print(query)


if __name__ == '__main__':
    workload = SsbQpsWorkload()
    queue = Queue()

    generate_thread = Thread(
        target=workload.generate_queries_with_distribution,
        args=(queue,),
        kwargs={
            'distribution': QpsWorkload.Distribution.UNIFORM,
            'qps': 1.0
        },
        name='QueryGenerator'
    )
    generate_thread.start()

    print_thread = Thread(
        target=print_queries,
        args=(queue,),
        name='QueryPrinter'
    )
    print_thread.start()
