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

import json
import os
from datetime import datetime, timezone
import pandas as pd
from pprint import pprint

import boto3

session = boto3.session.Session(region_name='ap-southeast-1')
client = session.client('cloudwatch')
paginator = client.get_paginator('get_metric_data')
with open(os.path.join(os.environ['RAVEN_HOME'], 'config', 'cloud', 'aws', 'cloudwatch',
                       'cloudwatch-metric-data-queries-for-t2-small.json'), encoding='utf-8') as file:
    metric_data_queries = json.load(file)
for metric_data_query in metric_data_queries:
    metric_data_query['MetricStat']['Metric']['Dimensions'].append({
        'Name': 'InstanceId',
        'Value': 'i-004b1618507eb2f05'
    })

start_time = datetime(2022, 1, 5, 14, 00, tzinfo=timezone.utc)
end_time = datetime(2022, 1, 5, 14, 35, tzinfo=timezone.utc)
response_iterator = paginator.paginate(
    MetricDataQueries=metric_data_queries,
    StartTime=start_time,
    EndTime=end_time,
    ScanBy='TimestampAscending'
)
metric: pd.DataFrame = pd.DataFrame()
for response in response_iterator:
    for metric_data_result in response['MetricDataResults']:
        df = pd.DataFrame(data={
            metric_data_result['Label']: metric_data_result['Values']
        }, index=metric_data_result['Timestamps'])
        metric = pd.concat([metric, df], axis=1, join='outer')
metric.to_csv('metric.csv')
