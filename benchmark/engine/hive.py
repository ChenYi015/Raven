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

from pyhive import hive
from pyhive.exc import OperationalError

import configs
from benchmark.core.engine import Engine
from benchmark.core.query import Query, Status

logger = configs.EXECUTE_LOGGER


class HiveEngine(Engine):

    def __init__(self, config: dict):
        super().__init__(config)

    def execute_query(self, query: Query) -> Query:
        logger.info(f'{self.name} engine is executing query: {query}.')
        cursor = hive.connect('localhost').cursor()
        try:
            cursor.execute_queries(f'use {query.database}')
            query.set_status(Status.EXECUTE)
            cursor.execute_queries(f'{query.sql}')
            cursor.fetchall()
            query.set_status(Status.FINISH)
            cursor.close()
            logger.info(f'{self.name} engine has finished executing query: {query}.')
        except OperationalError:
            query.set_status(Status.FAIL)
            logger.error(f'{self.name} engines failed to execute_queries query {query}, an error has occurred: {e}')
        return query
