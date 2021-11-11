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
import time
from enum import Enum


class QueryStatus(Enum):
    pass


class Query:

    def __init__(self, database: str, sql: str, name: str = None):
        self.name = name  # 查询名称
        self.database = database  # 数据库名称
        self.sql = sql  # 查询语句

        self.wait_start = None   # 查询进入请求队列时刻
        self.execute_start = None  # 查询开始执行时刻
        self.wait_time: float = 0.0  # 查询在请求队列中的等待时间
        self.response_time: float = 0.0  # 查询相应时间

    def update_wait_time(self):
        """更新查询在请求队列中的等待时间"""
        if self.wait_start is not None:
            self.wait_time = time.time() - self.wait_start

    def update_response_time(self):
        """更新查询响应时间"""
        if self.execute_start is not None:
            self.response_time = time.time() - self.execute_start

    def __str__(self):
        return f'Query(name={self.name}, database={self.database}, ' \
               f'wait_time={self.wait_time:.3f}, response_time={self.response_time:.3f})'
