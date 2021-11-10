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
from enum import Enum


class Event:

    class Type(Enum):
        ON_PM_QUERY_START = 'ON_PM_QUERY_START'
        ON_PM_QUERY_FINISH = 'ON_PM_QUERY_FINISH'
        ON_ETL_START = 'ON_ETL_START'
        ON_ETL_FINISH = 'ON_ETL_FINISH'
        ON_AM_QUERY_START = 'ON_AM_QUERY_START'
        ON_AM_QUERY_FINISH = 'ON_AM_QUERY_FINISH'

    def __init__(self, config: dict):
        self.name = config['Name']
        # 事件触发时刻(单位: 秒)
        self.time: float = 60 * 60 * config['Time']
        self.description = config['Description'] if 'Description' in config else ''

    def __str__(self):
        return f'Event {self.name}: {self.description}'


class Workload:

    class Type(Enum):
        PIPELINE = 'Pipeline'
        TIMELINE = 'Timeline'

    def __init__(self, config: dict):
        self.name = config['Name']
        self.type = config['Type']
        self.description = config['Description'] if 'Description' in config else ''

    def __str__(self):
        return f'{self.type}-based workload {self.name}: {self.description}'


class PipelineWorkload(Workload):

    def __init__(self, config: dict):
        super().__init__(config)

        # Queue of stages
        self.queue = Queue()
        for event_config in config['Events']:
            self.queue.put(Event(event_config))


class TimelineWorkload(Workload):

    def __init__(self, config: dict):
        super().__init__(config)

        # List of events
        self.events = []
        for event_config in config['Events']:
            self.events.append(Event(event_config))

    def append_event(self, event: Event):
        self.events.append(event)

    def pop_event(self) -> Event:
        return self.events.pop()
