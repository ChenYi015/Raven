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

import logging.config
import os
import time
from collections import deque

import yaml

from benchmark.core.engine import AbstractEngine
from benchmark.engines.kylin4.instance import KylinInstance
from benchmark.engines.kylin4.kylin import (
    launch_aws_kylin,
    destroy_aws_kylin,
    scale_aws_worker,
    scale_down_aws_worker
)


class Engine(AbstractEngine):

    def __init__(self):
        super().__init__()
        self._name = 'Kylin4'
        with open(os.path.join(os.environ['RAVEN_HOME'], 'configs', 'engines', 'kylin4', 'kylin.yaml')) as stream:
            config = yaml.safe_load(stream)
        self.config = config
        self.kylin_instance: KylinInstance = None
        self.is_ec2_cluster = self.config['DEPLOY_PLATFORM'] == 'ec2'
        self.server_mode = None
        # default alive workers num is 3, so scaling workers index must be bigger than 3
        self.standby_nodes = deque([4, 5])
        self.scaled_nodes = deque()

    def launch(self):
        logging.info(f'{self._name} is launching...')
        logging.info('Ec2: first launch Instances And Kylin nodes')
        self.kylin_instance = launch_aws_kylin(self.config)
        logging.info(f'{self._name} has launched.')

    def execute_query(self, database: str, query: str, name: str = None):
        logging.info(f'{self._name} is executing query: {name}.')
        start = time.time()

        # 执行查询
        response = self.kylin_instance.client.execute_query(database, query, 0, 100000)
        query_time = time.time() - start
        if response.get('isException') is None:
            logging.info(f'success, id: {id}, costTime: {query_time}')
        else:
            logging.info(f'failed, id: {id}, costTime: {query_time}')
        end = time.time()
        duration = end - start

        logging.info(f'Finish executing query {name}, {duration:.3f} seconds has elapsed.')
        return duration

    def shutdown(self):
        logging.info(f'{self._name} is shutting down...')
        logging.info('Ec2: destroy useless nodes')
        destroy_aws_kylin(self.config)
        logging.info(f'{self._name} has shut down. ')

    def scale_up_workers(self):
        try:
            scaled_worker_index = self.standby_nodes.popleft()
        except IndexError:
            logging.error(f'Current do not has any node to scale up.')
            return
        self.scaled_nodes.append(scaled_worker_index)
        scale_aws_worker(scaled_worker_index, self.config)

    def scale_down_workers(self):
        try:
            expected_down_node = self.scaled_nodes.popleft()
        except IndexError:
            logging.error(f'Current do not has any node to scale down.')
            return
        self.standby_nodes.append(expected_down_node)
        scale_down_aws_worker(expected_down_node)

    def prepare_historical_data(self):
        pass


if __name__ == '__main__':
    # Logging
    with open(os.path.join(os.environ['RAVEN_HOME'], 'configs', 'logging.yaml'), encoding='utf-8') as file:
        logging_config = yaml.load(file, Loader=yaml.FullLoader)
        logging.config.dictConfig(logging_config)

    engine = Engine()
    engine.launch()
