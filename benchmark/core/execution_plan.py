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


class ExecutionPlan(metaclass=abc.ABCMeta):

    def __init__(self):
        self._plan = None
        self._type = None
        self._context = None

    @abc.abstractmethod
    def build(self, conf):
        pass

    def start(self, engine, queries):
        self._plan.start(engine, queries)

    def get_metrics(self):
        return self._plan.get_metrics()