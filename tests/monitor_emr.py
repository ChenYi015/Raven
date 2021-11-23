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
from benchmark.providers.aws.provider import Provider

if __name__ == '__main__':
    aws = Provider(configs.PROVIDER_CONFIG)

    # 2021.11.20 SparkSQL SSB_1G Poisson
    cluster_id = 'j-14C9ADYKRYMMT'
    start = datetime.strptime('2021-11-24 08:38:52', '%Y-%m-%d %H:%M:%S')
    end = datetime.strptime('2021-11-24 09:38:57', '%Y-%m-%d %H:%M:%S')
    aws.monitor_emr(cluster_id=cluster_id, start=start, end=end)

    # 2021.11.20 Presto SSB_1G Poisson
    # cluster_id = 'j-H865R0POX8DO'
    # start = datetime.strptime('2021-11-24 08:16:50', '%Y-%m-%d %H:%M:%S')
    # end = datetime.strptime('2021-11-24 09:16:55', '%Y-%m-%d %H:%M:%S')
    # aws.monitor_emr(cluster_id=cluster_id, start=start, end=end)

    # 2021.11.20 SparkSQL SSB_1G Average
    # cluster_id = 'j-2NBEVP14KQYNB'
    # start = datetime.strptime('2021-11-23 08:16:27', '%Y-%m-%d %H:%M:%S')
    # end = datetime.strptime('2021-11-23 09:16:31', '%Y-%m-%d %H:%M:%S')
    # aws.monitor_emr(cluster_id=cluster_id, start=start, end=end)

    # 2021.11.20 SparkSQL SSB_1G Average
    # cluster_id = 'j-1UGFQ30ZCLF1R'
    # start = datetime.strptime('2021-11-23 07:41:02', '%Y-%m-%d %H:%M:%S')
    # end = datetime.strptime('2021-11-23 07:45:59', '%Y-%m-%d %H:%M:%S')
    # aws.monitor_emr(cluster_id=cluster_id, start=start, end=end)

    # 2021.11.20 SparkSQL SSB_1G Average
    # cluster_id = 'j-1CC40V21LD49H'
    # start = datetime.strptime('2021-11-20 14:45:07', '%Y-%m-%d %H:%M:%S')
    # end = datetime.strptime('2021-11-20 15:52:39', '%Y-%m-%d %H:%M:%S')
    # aws.monitor_emr(cluster_id=cluster_id, start=start, end=end)

    # 2021.11.19 Hive SSB_1G Average
    # cluster_id = 'j-274S7G207VVMM'
    # start = datetime.strptime('2021-11-19 13:30:29', '%Y-%m-%d %H:%M:%S')
    # end = datetime.strptime('2021-11-19 14:33:48', '%Y-%m-%d %H:%M:%S')
    # aws.monitor_emr(cluster_id=cluster_id, start=start, end=end)

    # 2021.11.18 Presto SSB_1G Average
    # cluster_id = 'j-13FNLO2JW79IE'
    # start = datetime.strptime('2021-11-18 13:56:24', '%Y-%m-%d %H:%M:%S')
    # end = datetime.strptime('2021-11-18 14:56:28', '%Y-%m-%d %H:%M:%S')
    # aws.monitor_emr(cluster_id=cluster_id, start=start, end=end)
