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

import abc
from queue import Queue


class Testplan(metaclass=abc.ABCMeta):
    class Type:
        PIPELINE = 'Pipeline'
        TIMELINE = 'Timeline'

    def __init__(self, config):
        self.name = config['Name']
        self.type = config['Type']
        self.description = config['Description'] if 'Description' in config else ''
        # self._plan = None
        # self._type = None
        # self._context = None

    # @abc.abstractmethod
    # def build(self, conf):
    #     pass

    # def start(self, engine, queries):
    #     self._plan.start(engine, queries)
    #
    # def get_metrics(self):
    #     return self._plan.get_metrics()


class Stage:

    def __init__(self, config: dict):
        pass


class Pipeline(Testplan):

    def __init__(self, config: dict):
        super().__init__(config)

        # Queue of stages
        self.queue = Queue()
        for event_config in config['Stages']:
            self.queue.put(Stage(event_config))
