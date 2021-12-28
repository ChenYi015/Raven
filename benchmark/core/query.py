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
from typing import Optional


class Status:
    """
    The status of query.
    """
    UNDEFINED = 'UNDEFINED '
    QUEUED = 'QUEUED'
    RUNNING = 'RUNNING'
    SUCCEEDED = 'SUCCEEDED'
    FAILED = ' FAILED'
    CANCELLED = 'CANCELLED'


class Query:

    def __init__(self, *, name: str = '', description: str = '', database: str, sql: str):
        """

        :param name: The query name.
        :param description: The query description.
        :param database: The database to which the query belongs.
        :param sql: The SQL query statements that comprise the query.
        """

        self.name = name
        self.description = description

        self.database = database
        self.sql = sql

        self._status = Status.UNDEFINED

        # 查询相关的时间戳
        self.wait_start: Optional[float] = None  # 查询进入等待队列时刻
        self.wait_finish: Optional[float] = None  # 查询离开等待队列时刻
        self.execute_start: Optional[float] = None  # 查询开始执行时刻
        self.execute_finish: Optional[float] = None  # 查询结束执行时刻

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status: Status):
        if status == Status.QUEUED:
            self.wait_start = time.time()
        elif status == Status.RUNNING:
            self.wait_finish = self.execute_start = time.time()
        elif status == Status.SUCCEEDED or status == Status.FAILED:
            self.execute_finish = time.time()
        else:
            raise ValueError('Wrong status.')
        self._status = status

    def __str__(self):
        words = [
            f"name='{self.name}'" if self.name else '',
            f"description='{self.description}'" if self.description else '',
            f"database='{self.database}'",
            f"status='{self._status}'",
        ]
        return 'Query(' + ', '.join(words) + ')'

    def get_queued_time_in_seconds(self) -> Optional[float]:
        if not self.wait_start or not self.wait_finish:
            return None
        else:
            return self.wait_finish - self.wait_start

    def get_running_time_in_seconds(self) -> Optional[float]:
        if not self.execute_start or not self.execute_finish:
            return None
        else:
            return self.execute_finish - self.execute_start

    def get_metrics(self) -> dict:
        return {
            'Name': self.name,
            'Description': self.description,
            'Database': self.database,
            'Sql': self.sql,
            'FinalStatus': self.status,
            'WaitStart': self.wait_start,
            'WaitFinish': self.wait_finish,
            'ExecuteStart': self.execute_start,
            'ExecuteFinish': self.execute_finish
        }
