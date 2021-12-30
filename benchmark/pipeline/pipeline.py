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

import logging

from benchmark.pipeline.context import Context


class Pipeline:
    def __init__(self):
        self.context = Context()
        self.valves = []

    def add_stage(self, valve):
        self.valves.append(valve)

    def start(self, engine, queries):
        self.context.setEngine(engine)
        self.context.setQueries(queries)
        if len(self.valves) == 0:
            logging.error("No valves available!")
        else:
            self.context.call(self.valves[self.get_first_valve_id()])

    def get_first_valve_id(self):
        for i, valve in enumerate(self.valves):
            if valve.is_first_valve is True:
                return i
        return 0

    def get_metrics(self):
        offline_metrics = []
        online_metrics = []
        for valve in self.valves:
            if valve.isOnline is True:
                online_metrics.append(valve.collect_metrics())
            else:
                offline_metrics.append(valve.collect_metrics())
        return offline_metrics, online_metrics
