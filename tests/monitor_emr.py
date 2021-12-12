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
import os
from datetime import datetime
from pprint import pprint

import configs
from benchmark.providers.aws.provider import Provider

if __name__ == '__main__':
    aws = Provider(configs.PROVIDER_CONFIG)
    logger = configs.ROOT_LOGGER

    # 2021.11.29 SparkSQL SSB_1G All distributions
    cluster_id = 'j-2Y4SF4KIBSQUM'
    start = datetime.strptime('2021-11-29 08:27:56', '%Y-%m-%d %H:%M:%S')
    end = datetime.strptime('2021-11-   29 11:45:39', '%Y-%m-%d %H:%M:%S')
    aws.monitor_emr(cluster_id=cluster_id, start=start, end=end)

    # 2021.11.28 SparkSQL SSB_1G All distributions
    # cluster_id = 'j-368XNKCPWCH7B'
    # run = datetime.strptime('2021-11-27 05:44:53', '%Y-%m-%d %H:%M:%S')
    # end = datetime.strptime('2021-11-28 20:28:39', '%Y-%m-%d %H:%M:%S')
    # master_dict = {
    #     'InstanceId': 'i-04cbf0cb1f471f635',
    #     'ImageId': 'ami-06fc9324a2ebf26bc',
    #     'InstanceType': 'm5.xlarge'
    # }
    # metric = aws.get_ec2_metrics(master_dict, run, end)
    # output_dir = os.path.join(os.environ['RAVEN_HOME'], 'out', f'emr_{cluster_id}', 'metrics')
    # try:
    #     os.makedirs(output_dir, exist_ok=True)
    # except OSError as error:
    #     logger.error(error)
    # with open(os.path.join(output_dir, f'master_{master_dict["InstanceId"]}.metrics'), mode='w',
    #           encoding='utf-8') as file:
    #     pprint(metric, stream=file, indent=2)
    #
    # core_dicts = [
    #     {
    #         'InstanceId': 'i-08103a70aa0ff8679',
    #         'ImageId': 'ami-06fc9324a2ebf26bc',
    #         'InstanceType': 'm5.2xlarge'
    #     }, {
    #         'InstanceId': 'i-0e6cf9bde96e5e977',
    #         'ImageId': 'ami-06fc9324a2ebf26bc',
    #         'InstanceType': 'm5.2xlarge'
    #     }, {
    #         'InstanceId': 'i-090bf70a19bb39f4a',
    #         'ImageId': 'ami-06fc9324a2ebf26bc',
    #         'InstanceType': 'm5.2xlarge'
    #     }, {
    #         'InstanceId': 'i-01770319edcbfc2ca',
    #         'ImageId': 'ami-06fc9324a2ebf26bc',
    #         'InstanceType': 'm5.2xlarge'
    #     }, {
    #         'InstanceId': 'i-05fd29d3375798e29',
    #         'ImageId': 'ami-06fc9324a2ebf26bc',
    #         'InstanceType': 'm5.2xlarge'
    #     }, {
    #         'InstanceId': 'i-0da6dd82a9b88ec28',
    #         'ImageId': 'ami-06fc9324a2ebf26bc',
    #         'InstanceType': 'm5.2xlarge'
    #     }, {
    #         'InstanceId': 'i-0c210ce24b87868c3',
    #         'ImageId': 'ami-06fc9324a2ebf26bc',
    #         'InstanceType': 'm5.2xlarge'
    #     }, {
    #         'InstanceId': 'i-0dacb58f04231b7bc',
    #         'ImageId': 'ami-06fc9324a2ebf26bc',
    #         'InstanceType': 'm5.2xlarge'
    #     }, {
    #         'InstanceId': 'i-070d5211e16c52223',
    #         'ImageId': 'ami-06fc9324a2ebf26bc',
    #         'InstanceType': 'm5.2xlarge'
    #     }, {
    #         'InstanceId': 'i-0a513c80d61b297ac',
    #         'ImageId': 'ami-06fc9324a2ebf26bc',
    #         'InstanceType': 'm5.2xlarge'
    #     }
    # ]
    # for core_dict in core_dicts:
    #     metric = aws.get_ec2_metrics(core_dict, run, end)
    #     with open(os.path.join(output_dir, f'core_{core_dict["InstanceId"]}.metrics'), mode='w',
    #               encoding='utf-8') as file:
    #         pprint(metric, stream=file, indent=2)



    # 2021.11.28 Presto SSB_1G All distributions
    # cluster_id = 'j-RIQLYZZKJKU6'
    # run = datetime.strptime('2021-11-28 02:15:39', '%Y-%m-%d %H:%M:%S')
    # end = datetime.strptime('2021-11-28 04:40:26', '%Y-%m-%d %H:%M:%S')
    # aws.monitor_emr(cluster_id=cluster_id, run=run, end=end)

    # 2021.11.25 Presto SSB_1G Poisson
    # cluster_id = 'j-2H4N9NH2GM3Y0'
    # run = datetime.strptime('2021-11-25 10:34:10', '%Y-%m-%d %H:%M:%S')
    # end = datetime.strptime('2021-11-25 11:34:16', '%Y-%m-%d %H:%M:%S')
    # aws.monitor_emr(cluster_id=cluster_id, run=run, end=end)

    # 2021.11.25 Presto SSB_1G Average
    # cluster_id = 'j-2V9WGFLPGGKDQ'
    # run = datetime.strptime('2021-11-25 07:35:26', '%Y-%m-%d %H:%M:%S')
    # end = datetime.strptime('2021-11-25 08:35:30', '%Y-%m-%d %H:%M:%S')
    # aws.monitor_emr(cluster_id=cluster_id, run=run, end=end)

    # 2021.11.24 SparkSQL SSB_1G Poisson
    # cluster_id = 'j-14C9ADYKRYMMT'
    # run = datetime.strptime('2021-11-24 08:38:52', '%Y-%m-%d %H:%M:%S')
    # end = datetime.strptime('2021-11-24 09:38:57', '%Y-%m-%d %H:%M:%S')
    # aws.monitor_emr(cluster_id=cluster_id, run=run, end=end)

    # 2021.11.20 Presto SSB_1G Poisson
    # cluster_id = 'j-H865R0POX8DO'
    # run = datetime.strptime('2021-11-24 08:16:50', '%Y-%m-%d %H:%M:%S')
    # end = datetime.strptime('2021-11-24 09:16:55', '%Y-%m-%d %H:%M:%S')
    # aws.monitor_emr(cluster_id=cluster_id, run=run, end=end)

    # 2021.11.20 SparkSQL SSB_1G Average
    # cluster_id = 'j-2NBEVP14KQYNB'
    # run = datetime.strptime('2021-11-23 08:16:27', '%Y-%m-%d %H:%M:%S')
    # end = datetime.strptime('2021-11-23 09:16:31', '%Y-%m-%d %H:%M:%S')
    # aws.monitor_emr(cluster_id=cluster_id, run=run, end=end)

    # 2021.11.20 SparkSQL SSB_1G Average
    # cluster_id = 'j-1UGFQ30ZCLF1R'
    # run = datetime.strptime('2021-11-23 07:41:02', '%Y-%m-%d %H:%M:%S')
    # end = datetime.strptime('2021-11-23 07:45:59', '%Y-%m-%d %H:%M:%S')
    # aws.monitor_emr(cluster_id=cluster_id, run=run, end=end)

    # 2021.11.20 SparkSQL SSB_1G Average
    # cluster_id = 'j-1CC40V21LD49H'
    # run = datetime.strptime('2021-11-20 14:45:07', '%Y-%m-%d %H:%M:%S')
    # end = datetime.strptime('2021-11-20 15:52:39', '%Y-%m-%d %H:%M:%S')
    # aws.monitor_emr(cluster_id=cluster_id, run=run, end=end)

    # 2021.11.19 Hive SSB_1G Average
    # cluster_id = 'j-274S7G207VVMM'
    # run = datetime.strptime('2021-11-19 13:30:29', '%Y-%m-%d %H:%M:%S')
    # end = datetime.strptime('2021-11-19 14:33:48', '%Y-%m-%d %H:%M:%S')
    # aws.monitor_emr(cluster_id=cluster_id, run=run, end=end)

    # 2021.11.18 Presto SSB_1G Average
    # cluster_id = 'j-13FNLO2JW79IE'
    # run = datetime.strptime('2021-11-18 13:56:24', '%Y-%m-%d %H:%M:%S')
    # end = datetime.strptime('2021-11-18 14:56:28', '%Y-%m-%d %H:%M:%S')
    # aws.monitor_emr(cluster_id=cluster_id, run=run, end=end)
