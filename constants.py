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


GITHUB_REPO_URL = 'https://github.com/ChenYi015/Raven.git'


class Engine:
    """Engine names."""
    HIVE = 'hive'
    SPARK_SQL = 'spark-sql'
    PRESTO = 'presto'
    ATHENA = 'athena'


class Workload:
    """Workload names."""
    TPC_H = 'tpc-h'
    TPC_DS = 'tpc-ds'
    SSB = 'ssb'