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
import time
from threading import Thread

from benchmark.lib.popen import subprocess_popen


class Valve:
    def __init__(self):
        self.next = None
        self.is_first_valve = False
        self.metrics = []

        self.name = "New stage"
        self.description = ""
        self.isOnline = False

        self.concurrency = 1

    def set_next(self, next):
        self.next = next

    def set_first_stage(self):
        self.is_first_valve = True

    def run(self, context):
        threads = []
        for i in range(self.concurrency):
            threads.append(Thread(target=self.run_thread, args=(context, i)))
        logging.info("Starting threads...")
        for thread in threads:
            thread.start()
        logging.info("Waiting for all threads to finish...")
        for thread in threads:
            thread.join()
        logging.info("All threads finished!")
        logging.info("Stage finished!")
        logging.info("--------------------------------")

    def run_thread(self, context, thread_id):
        pass

    def get_metrics(self):
        return self.metrics


class OfflineStage(Valve):
    def __init__(self, config):
        super().__init__()
        self.name = config['name']
        self.description = config['description']
        self.commands = config['commands']
        self.concurrency = config['concurrency']

    def run_thread(self, context, thread_id):
        for item in self.commands:
            try:
                command = 'cd ' + item['path'] + ' && ' + item['command']
            except KeyError:
                command = item['command']
            start = time.time()
            subprocess_popen(command)
            finish = time.time()
            summary = {'threadID': str(thread_id), 'command': command, 'run': start, 'finish': finish}
            self.metrics.append(summary)


class OnlineStage(Valve):
    def __init__(self, config):
        super().__init__()
        self.name = config['name']
        self.description = config['description']
        self.queries = config['queries']
        self.isOnline = True
        self.concurrency = config['concurrency']
        self.loop = config['loop']

    def run_thread(self, context, thread_id):
        context.engine.query(context.queries['database'])
        for i in range(self.loop):
            for query in self.queries:
                for matching_query in context.queries['sql']:
                    if matching_query['name'] == query:
                        sql = matching_query['sql']
                        start = time.time()
                        if sql == 'sqls':
                            sqls = matching_query['sqls']
                            for sql in sqls:
                                context.engine.query(sql)
                        else:
                            context.engine.query(sql)
                        finish = time.time()
                        summary = {'threadID': str(thread_id), 'query': query, 'run': start, 'finish': finish}
                        self.metrics.append(summary)
                        logging.info("Execution of " + query + " complete.")
