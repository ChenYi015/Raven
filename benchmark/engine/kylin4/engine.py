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
from collections import deque
from typing import Optional

import yaml

import configs
from benchmark.core.engine import Engine
from benchmark.core.query import Query, Status
from benchmark.engine.kylin4.libs.instance import KylinInstance
from benchmark.engine.kylin4.libs.kylin import (
    launch_aws_kylin,
    destroy_aws_kylin,
    scale_aws_worker,
    scale_down_aws_worker
)

logger = configs.EXECUTE_LOGGER


class Engine(Engine):

    def __init__(self, config: dict):
        super().__init__(config)
        self._name = 'Kylin4'
        self.config = None
        with open(os.path.join(os.environ['RAVEN_HOME'], 'benchmark', 'engines', 'kylin4', 'configs', 'kylin.yaml')) as stream:
            self.config = yaml.load(stream, Loader=yaml.FullLoader)
        self.kylin_instance: Optional[KylinInstance] = None
        self.is_ec2_cluster = self.config['DEPLOY_PLATFORM'] == 'ec2'
        self.server_mode = None
        # default alive workers num is 3, so scaling workers index must be bigger than 3
        self.standby_nodes = deque([4, 5])
        self.scaled_nodes = deque()

    def launch(self):
        logger.info(f'{self._name} is launching...')
        self.kylin_instance = launch_aws_kylin(self.config)
        logger.info(f'{self._name} has launched.')

    def execute_query(self, query: Query) -> Query:
        logger.info(f'{self._name} is executing query: {query}.')
        # 执行查询
        query.set_status(Status.EXECUTE)
        response = self.kylin_instance.client.execute_query(
            project=query.database,
            sql=query.sql,
            offset=0,
            timeout=30
        )
        # print(response)
        if not response.get('isException'):
            query.set_status(Status.FINISH)
            logger.info(f'{self.name} engine has finished executing query: {query}.')
        else:
            query.set_status(Status.FAIL)
            logger.error(f'{self.name} engines failed to execute_queries query {query}, an error has occurred.')
        return query

    def shutdown(self):
        logger.info(f'{self._name} is shutting down...')
        # destroy_aws_kylin(self.config)
        logger.info(f'{self._name} has shut down. ')

    def scale_up_workers(self):
        try:
            scaled_worker_index = self.standby_nodes.popleft()
        except IndexError:
            logger.error(f'Current do not has any node to scale up.')
            return
        self.scaled_nodes.append(scaled_worker_index)
        scale_aws_worker(scaled_worker_index, self.config)

    def scale_down_workers(self):
        try:
            expected_down_node = self.scaled_nodes.popleft()
        except IndexError:
            logger.error(f'Current do not has any node to scale down.')
            return
        self.standby_nodes.append(expected_down_node)
        scale_down_aws_worker(expected_down_node)

    def prepare_historical_data(self):
        pass


if __name__ == '__main__':
    with open(os.path.join(os.environ['RAVEN_HOME'], 'configs', 'raven.yaml'), mode='r', encoding='utf-8') as file:
        raven_config = yaml.load(file, Loader=yaml.FullLoader)
    engine = Engine(config=raven_config['Engine'])
    engine.launch()
