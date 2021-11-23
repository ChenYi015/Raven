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
    path = configs.WORKLOAD_CONFIG['ConfigPath']
    with open(os.path.join(os.environ['RAVEN_HOME'], *path.split('/'))) as _:
        workload_config = yaml.load(_, yaml.FullLoader)
    workload = Workload(workload_config)
    workload.concurrency = configs.WORKLOAD_CONFIG['Concurrency']
    execute_queue = Queue()
    workload.generate(execute_queue, distribution='poisson')
