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
import logging


class Context:
    """
    The pipeline context.
    """
    def __init__(self):
        self.engine = None


class Stage(metaclass=abc.ABCMeta):

    def __init__(self):
        self.type = None

    @abc.abstractmethod
    def run(self, context):
        pass


class OfflineStage(Stage):

    def __init__(self, config):
        super().__init__()
        self.type = 'offline'

    def run(self, context: Context):
        pass


class OnlineStage(Stage):

    def __init__(self, config):
        super().__init__()
        self.name = config['Name']
        self.description = config['Description']
        self.type = config['OnLine']
        self.concurrency = config['Concurrency']
        self.loop = config['Loop']
        self.queries = config['Queries']

    def run(self, context):
        self.context.engine.submit_query()

    def run_thread(self, context, thread_id):
        context.engine.submit_query()


class Pipeline:
    """
    Streaming workflow with pipeline.

    Parameters
    ----------
    verbose : bool, default=False
        If True, the time elapsed while fitting each step will be printed as it
        is completed.
    """

    def __init__(self, *, verbose=False):
        self._stages = []
        self._context = None
        self._verbose = verbose

    def __len__(self):
        """
        Returns the length of the Pipeline
        """
        return len(self._stages)

    @property
    def stages(self):
        return self._stages

    def append_stage(self, stage):
        self._stages.append(stage)

    def set_context(self, context):
        self._context = context

    def run(self, context):
        for stage in self._stages:
            stage.run(context)
