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

import prestodb
import yaml


class PrestoEngine:

    def __init__(self):
        super().__init__()
        self._cursor = None

    def launch(self):
        pass

    def execute_query(self, database: str, sql: str, name: str = None):
        self._cursor = prestodb.dbapi.connect(
            host='localhost',
            port=8889,
            user='hadoop',
            catalog='hive',
            schema=database
        ).cursor()
        try:
            print(f'Now executing {name}...')
            self._cursor.execute(f'{sql}')
            print(self._cursor.fetchall())
        except Exception:
            print(f'An error occurred when executing {name}.')

    def shutdown(self):
        self._cursor.close()
        self._cursor = None


if __name__ == '__main__':
    engine = PrestoEngine()
    engine.launch()
    with open('../configs/workloads/ssb.yaml', encoding='utf-8') as file:
        workload = yaml.load(file, yaml.FullLoader)
    database = workload['Database']
    for query in workload['Queries']:
        sql = query['SQL']
        name = query['Name']
        engine.execute_query(database=database, sql=sql, name=name)
