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

import os
from queue import Queue

import yaml

import configs
from benchmark.core.workload import Workload

if __name__ == '__main__':
    rel_path = configs.WORKLOAD_CONFIG['ConfigPath']
    path = os.path.join(os.environ['RAVEN_HOME'], rel_path)
    with open(path, encoding='utf-8') as stream:
        workload_config = yaml.load(stream=stream, Loader=yaml.FullLoader)
    workload = Workload(workload_config)
    queue = Queue()
    workload.generate_queries(
        execute_queue=queue,
        distribution=Workload.Distribution.UNIMODAL,
        duration=60.0,
        max_queries=10000,
        collect_data=True
    )
