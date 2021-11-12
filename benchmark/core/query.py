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
from typing import Optional

from benchmark.core.metric import Metric


class Status:
    GENERATE = 'generate'
    WAIT = 'wait'
    EXECUTE = 'execute'
    FINISH = 'finish'
    FAIL = 'fail'


class Query:

    def __init__(self, database: str, sql: str, name: str = None):
        self.name = name  # 查询名称
        self.database = database  # 数据库名称
        self.sql = sql  # 查询语句

        self.status = Status.GENERATE

        # 查询相关的时间戳
        self.generate: float = time.time()  # 查询生成时刻
        self.wait_start: Optional[float] = None  # 查询进入请求队列时刻
        self.wait_finish: Optional[float] = None  # 查询离开请求队列时刻
        self.execute_start: Optional[float] = None  # 查询开始执行时刻
        self.execute_finish: Optional[float] = None  # 查询结束执行时刻

        self.reaction_time: Optional[float] = None  # 查询在请求队列中的等待时间
        self.latency: Optional[float] = None
        self.response_time: Optional[float] = None  # 查询相应时间

    def set_status(self, status: Status):
        self.status = status
        if status == Status.WAIT:
            self.wait_start = time.time()
        elif status == Status.EXECUTE:
            self.wait_finish = self.execute_start = time.time()
            self.reaction_time = self.wait_finish - self.wait_start
        elif status == Status.FINISH or status == Status.FAIL:
            self.execute_finish = time.time()
            self.latency = self.execute_finish - self.execute_start
            self.response_time = self.execute_finish - self.wait_start
        else:
            raise ValueError('Wrong status.')

    def get_metric_dict(self) -> dict:
        """Get query metrics in dict."""
        return {
            'name': self.name,
            'database': self.database,
            'sql': self.sql,
            'generate': self.generate,
            'wait_start': self.wait_start,
            'wait_finish': self.wait_finish,
            'execute_start': self.execute_start,
            'execute_finish': self.execute_finish,
            Metric.REACTION_TIME: self.reaction_time,
            Metric.LATENCY: self.latency,
            Metric.RESPONSE_TIME: self.response_time,
            'status': self.status
        }

    def __str__(self):
        return f'''Query(name={self.name}, database={self.database}, status={self.status}, generate={self.generate:.3f}, 
    wait_start={self.wait_start}, wait_finish={self.wait_finish}, reaction_time={self.reaction_time},
    execute_start={self.execute_start}, execute_finish={self.execute_finish}, latency={self.latency}, response_time={self.response_time})'''


if __name__ == '__main__':
    query = Query(
        database='test_db',
        sql='SELECT * FROM test_table',
        name='query_1'
    )
    print(query)