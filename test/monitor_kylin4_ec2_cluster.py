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

from datetime import datetime

import configs
from benchmark.cloud.provider import Provider

if __name__ == '__main__':
    # AWS Cloud Provider
    aws = Provider(configs.PROVIDER_CONFIG)

    # 2021.12.13 Kylin4 SSB 1GB
    master_instance_id = 'i-0642b9bbace9d9a96'
    start = datetime.strptime('2021-12-13 05:10:47', '%Y-%m-%d %H:%M:%S')
    end = datetime.strptime('2021-12-13 06:20:11', '%Y-%m-%d %H:%M:%S')
    aws.monitor_kylin4_ec2_cluster(master_instance_id=master_instance_id, start=start, end=end)
