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
from datetime import datetime

import pytz

import configs
from benchmark.providers.aws.provider import Provider

if __name__ == '__main__':
    aws = Provider(configs.PROVIDER_CONFIG)

    cluster_id = aws.create_and_setup_emr_for_engine('spark-3.1.1-sql')

    start = datetime.now(pytz.timezone('utc'))
    time.sleep(60 * 15)
    end = datetime.now(pytz.timezone('utc'))

    aws.monitor_emr(cluster_id=cluster_id, start=start, end=end)
