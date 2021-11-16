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
import logging.config
import os
from datetime import datetime, timedelta
from typing import List

import boto3
import botocore.exceptions
import numpy as np
import pytz
import yaml


def get_metrics_from_cloudwatch_agent(start: datetime, end: datetime) -> List[dict]:
    """
    Get metrics from AWS CloudWatchAgent.
    :param start: 开始时间戳
    :param end: 结束时间戳
    :return:
    """
    client = boto3.client('ec2')
    response = client.describe_instances(
        Filters=[
            {
                'Name': 'tag:Project',
                'Values': ['Raven']
            }
        ]
    )
    metrics = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            if instance['State']['Name'] == 'running':
                metric = get_metrics_by_instance(instance, start, end)
                metrics.append(metric)
    return metrics


def get_metrics_by_instance(instance: dict, start: datetime, end: datetime) -> dict:
    """
    Get metrics from AWS CloudWatchAgent by instance.
    :param instance:
    :param start:
    :param end:
    :return:
        {
            'Id': 'string',
            'Label': 'string',
            'Timestamps': [
                datetime(2015, 1, 1),
            ],
            'Values': [
                123.0,
            ],
            'StatusCode': 'Complete'|'InternalError'|'PartialData',
            'Messages': [
                {
                    'Code': 'string',
                    'Value': 'string'
                },
            ]
        }
    """

    client = boto3.client('cloudwatch')

    with open(os.path.join(os.environ['RAVEN_HOME'], 'configs', 'providers', 'aws',
                           'cloudwatch-metric-data-queries-ec2.json'), mode='r', encoding="utf-8") as _:
        metric_data_queries = json.load(_)

    for metric_data_query in metric_data_queries:
        metric_data_query['MetricStat']['Metric']['Dimensions'].append({
            'Name': 'InstanceId',
            'Value': instance['InstanceId']
        })
        metric_data_query['MetricStat']['Metric']['Dimensions'].append({
            'Name': 'ImageId',
            'Value': instance['ImageId']
        })
        metric_data_query['MetricStat']['Metric']['Dimensions'].append({
            'Name': 'InstanceType',
            'Value': instance['InstanceType']
        })

    try:
        response = client.get_metric_data(
            MetricDataQueries=metric_data_queries,
            StartTime=start,
            EndTime=end
        )
        return response
    except botocore.exceptions.ClientError as error:
        logging.error(error.response)


def analyze(metrics, timestamps):
    global_conf_file = open("config/config.yaml", encoding="UTF-8")
    global_conf = yaml.load(global_conf_file, Loader=yaml.FullLoader)
    try:
        type = global_conf['metrics']
    except KeyError:
        logging.error("Failed: incomplete key-value pairs")
        return
    try:
        conf_file = open("config/metrics/" + global_conf['metrics'] + ".yaml", encoding="UTF-8")
        conf = yaml.load(conf_file, Loader=yaml.FullLoader)
    except FileNotFoundError:
        logging.error("Failed: invalid metrics type")
        return

    offline_times = []
    for command in timestamps['offline']:
        offline_times.append(command['finish'] - command['start'])
    online_times = []
    for query in timestamps['online']:
        online_times.append(query['finish'] - query['start'])

    # A. time-related metrics
    # A1. overall query speed
    if 'time_tot_offline' in conf['metrics']:
        time_tot_offline = np.sum(offline_times)
    if 'time_tot_online' in conf['metrics']:
        time_tot_online = np.sum(online_times)
    if 'time_avg_offline' in conf['metrics']:
        time_avg_offline = np.average(offline_times)
    if 'time_avg_online' in conf['metrics'] or 'queries_per_second' in conf['metrics']:
        time_avg_online = np.average(online_times)
        queries_per_second = 1.0 / time_avg_online

    # A2. query bottlenecks
    if 'time_max_online' in conf['metrics']:
        time_max_online = np.max(online_times)
    if 'time_99th_quantile' in conf['metrics'] or 'time_95th_quantile' in conf['metrics'] \
            or 'time_90th_quantile' in conf['metrics'] or 'time_median_online' in conf['metrics']:
        time_99th_quantile = np.percentile(online_times, 99)
        time_95th_quantile = np.percentile(online_times, 95)
        time_90th_quantile = np.percentile(online_times, 90)
        time_median_online = np.percentile(online_times, 50)

    # A3. Query time distribution
    if 'time_between_queries' in conf['metrics']:
        temp_time_tot_online = 0
        temp_query_start = 0
        temp_query_finish = 0
        for query in timestamps['online']:
            if query['finish'] > temp_query_finish:
                temp_query_finish = query['finish']
            if query['start'] < temp_query_start or temp_query_start == 0:
                temp_query_start = query['start']
            temp_time_tot_online += query['finish'] - query['start']
        time_between_queries = temp_query_finish - temp_query_start - temp_time_tot_online
    if 'time_variation_per_query' in conf['metrics']:
        time_variation_per_query = np.std(online_times)

    # A4. Accordance for concurrent jobs
    pass

    # B. Resource Usage
    # B1. used resources & free time
    if 'cpu_avg_online' in conf['metrics'] or 'cpu_free_time' in conf['metrics']:
        temp_cpu_avg_online = 0
        temp_cpu_avg_online_cnt = 0
        for instance in metrics:
            for metric in instance:
                if metric['Label'] == "cpu_usage_user":
                    for i in range(len(metric['Timestamps'])):
                        time = metric['Timestamps'][i]
                        if start <= time <= finish:
                            temp_cpu_avg_online += metric['Values'][i]
                            temp_cpu_avg_online_cnt += 1
        cpu_avg_online = temp_cpu_avg_online / temp_cpu_avg_online_cnt * 0.01
        cpu_free_time = (finish - start) * (1 - cpu_avg_online)
    if 'mem_avg_online' in conf['metrics'] or 'mem_free_time' in conf['metrics']:
        temp_mem_avg_online = 0
        temp_mem_avg_online_cnt = 0
        for instance in metrics:
            for metric in instance:
                if metric['Label'] == "mem_used_percent":
                    for i in range(len(metric['Timestamps'])):
                        time = metric['Timestamps'][i]
                        if start <= time <= finish:
                            temp_mem_avg_online += metric['Values'][i]
                            temp_mem_avg_online_cnt += 1
        mem_avg_online = temp_mem_avg_online / temp_mem_avg_online_cnt * 0.01
        mem_free_time = (finish - start) * (1 - mem_avg_online)

    # B2. Load balance
    if 'cpu_load_balance' in conf['metrics']:
        temp_cpu_average_loads = []
        for instance in metrics:
            temp_cpu_avg_online = 0
            temp_cpu_avg_online_cnt = 0
            for metric in instance:
                if metric['Label'] == "cpu_usage_user":
                    for i in range(len(metric['Timestamps'])):
                        time = metric['Timestamps'][i]
                        if start <= time <= finish:
                            temp_cpu_avg_online += metric['Values'][i]
                            temp_cpu_avg_online_cnt += 1
            temp_cpu_average_loads.append(temp_cpu_avg_online / temp_cpu_avg_online_cnt * 0.01)
        cpu_load_balance = np.std(temp_cpu_average_loads)

    if 'mem_load_balance' in conf['metrics']:
        temp_mem_average_loads = []
        for instance in metrics:
            temp_mem_avg_online = 0
            temp_mem_avg_online_cnt = 0
            for metric in instance:
                if metric['Label'] == "mem_used_percent":
                    for i in range(len(metric['Timestamps'])):
                        time = metric['Timestamps'][i]
                        if start <= time <= finish:
                            temp_mem_avg_online += metric['Values'][i]
                            temp_mem_avg_online_cnt += 1
            temp_mem_average_loads.append(temp_mem_avg_online / temp_mem_avg_online_cnt * 0.01)
        mem_load_balance = np.std(temp_mem_average_loads)

    # B3. I/O efficiency
    if 'io_avg_time' in conf['metrics']:
        temp_io_avg_time = 0
        temp_io_avg_online_cnt = 0
        for instance in metrics:
            for metric in instance:
                if metric['Label'] == "io_time":
                    for i in range(len(metric['Timestamps'])):
                        time = metric['Timestamps'][i]
                        if start <= time <= finish:
                            temp_io_avg_time += metric['Values'][i]
                            temp_io_avg_online_cnt += 1
        io_avg_time = temp_io_avg_time / temp_io_avg_online_cnt * 0.01

    if 'disk_usage' in conf['metrics']:
        temp_disk_usage = 0
        temp_disk_usage_cnt = 0
        for instance in metrics:
            for metric in instance:
                if metric['Label'] == "disk_used":
                    for i in range(len(metric['Timestamps'])):
                        time = metric['Timestamps'][i]
                        if start <= time <= finish:
                            temp_disk_usage += metric['Values'][i]
                            temp_disk_usage_cnt += 1
        disk_usage = temp_disk_usage / temp_disk_usage_cnt * 0.01

    # C. Bill prediction

    offline_calculation_overhead = eval(str(conf['offline']['calculation']['eval']))
    offline_delay_overhead = eval(str(conf['offline']['delay']['eval']))
    online_calculation_overhead = eval(str(conf['online']['calculation']['eval']))
    online_delay_overhead = eval(str(conf['online']['delay']['eval']))
    # name = np.array(['Offline calculation', 'Offline delay', 'Online calculation', 'Online delay'])
    # value = np.array([offline_calculation_overhead, offline_delay_overhead, online_calculation_overhead, online_delay_overhead])
    # theta = np.concatenate((theta, [theta[0]]))
    # value = np.concatenate((value, [value[0]]))
    # name = np.array(['CPU idle', 'Memory idle', 'CPU skew', 'Memory skew'])
    # theta = np.linspace(0, 2 * np.pi, len(name), endpoint=False)
    # value = np.array([1 - cpu_avg_online, 1 - mem_avg_online, cpu_load_balance, mem_load_balance])
    # ax = plt.subplot(111, projection='polar')
    # ax.plot(theta, value, 'm-', lw=1, alpha=0.75)
    # ax.fill(theta, value, 'm', alpha=0.75)
    # ax.set_thetagrids(theta * 180 / np.pi, name)
    # ax.set_theta_zero_location('N')
    # ax.set_ylim(0,1)
    # ax.set_title('Benchmark Results - resources', fontsize=20)
    # plt.show()
    logging.debug("--------------------------------")
    if 'time_tot_offline' in conf['metrics']:
        logging.debug("time_tot_offline: " + str(time_tot_offline))
    if 'time_tot_online' in conf['metrics']:
        logging.debug("time_tot_online: " + str(time_tot_online))
    if 'time_avg_offline' in conf['metrics']:
        logging.debug("time_avg_offline: " + str(time_avg_offline))
    if 'time_avg_online' in conf['metrics'] or 'queries_per_second' in conf['metrics']:
        logging.debug("time_avg_online: " + str(time_avg_online))
        logging.debug("queries_per_second: " + str(queries_per_second))
    if 'time_max_online' in conf['metrics']:
        logging.debug("time_max_online: " + str(time_max_online))
    if 'time_99th_quantile' in conf['metrics'] or 'time_95th_quantile' in conf['metrics'] \
            or 'time_90th_quantile' in conf['metrics'] or 'time_median_online' in conf['metrics']:
        logging.debug("time_99th_quantile: " + str(time_99th_quantile))
        logging.debug("time_95th_quantile: " + str(time_95th_quantile))
        logging.debug("time_90th_quantile: " + str(time_90th_quantile))
        logging.debug("time_median_online: " + str(time_median_online))
    if 'time_between_queries' in conf['metrics']:
        logging.debug("time_between_queries: " + str(time_between_queries))
    if 'time_variation_per_query' in conf['metrics']:
        logging.debug("time_variation_per_query: " + str(time_variation_per_query))
    if 'cpu_avg_online' in conf['metrics'] or 'cpu_free_time' in conf['metrics']:
        logging.debug("cpu_avg_online: " + str(cpu_avg_online))
        logging.debug("cpu_free_time: " + str(cpu_free_time))
    if 'mem_avg_online' in conf['metrics'] or 'mem_free_time' in conf['metrics']:
        logging.debug("mem_avg_online: " + str(mem_avg_online))
        logging.debug("mem_free_time: " + str(mem_free_time))
    if 'cpu_load_balance' in conf['metrics']:
        logging.debug("cpu_load_balance: " + str(cpu_load_balance))
    if 'mem_load_balance' in conf['metrics']:
        logging.debug("mem_load_balance: " + str(mem_load_balance))
    if 'io_avg_time' in conf['metrics']:
        logging.debug("io_avg_time: " + str(io_avg_time))
    if 'disk_usage' in conf['metrics']:
        logging.debug("disk_usage: " + str(disk_usage))
        disk_usage = temp_disk_usage / temp_disk_usage_cnt * 0.01
    logging.info("--------------------------------")
    logging.info("Offline calculation overhead: " + str(round(offline_calculation_overhead, 3)))
    logging.info("Offline delay overhead: " + str(round(offline_delay_overhead, 3)))
    logging.info("--------------------------------")
    logging.info("Online calculation overhead: " + str(round(online_calculation_overhead, 3)))
    logging.info("Online delay overhead: " + str(round(online_delay_overhead, 3)))
    logging.info("--------------------------------")
    overhead = eval(str(conf['total']['eval']))
    logging.info("Total overhead: " + str(round(overhead, 3)))
    return overhead


if __name__ == '__main__':
    # Logging
    with open(os.path.join(os.environ['RAVEN_HOME'], 'configs', 'logging.yaml'), encoding='utf-8') as file:
        logging_config = yaml.load(file, Loader=yaml.FullLoader)
        logging.config.dictConfig(logging_config)

    end = datetime.now(pytz.timezone('utc'))
    start = end - timedelta(minutes=15)

    from pprint import pprint

    metrics = get_metrics_from_cloudwatch_agent(start=start, end=end)
    pprint(metrics)

# if __name__ == '__main__':
#     if len(sys.argv) == 2:
#         t = {}
#         with open("./metrics/offline_times", 'r', encoding='utf-8') as f:
#             t['offline'] = json.loads(f.read().replace("'", "\""))
#         with open("./metrics/online_times", 'r', encoding='utf-8') as f:
#             t['online'] = json.loads(f.read().replace("'", "\""))
#         start = -1
#         finish = -1
#         for item in t['offline']:
#             if start == -1 or (start != -1 and item['start'] < start):
#                 start = item['start']
#             if finish == -1 or (finish != -1 and item['finish'] > finish):
#                 finish = item['finish']
#         for item in t['online']:
#             if start == -1 or (start != -1 and item['start'] < start):
#                 start = item['start']
#             if finish == -1 or (finish != -1 and item['finish'] > finish):
#                 finish = item['finish']
#         if sys.argv[1] == '-1':
#             logging.warning("Cluster ID not specified. Use current metrics directly.")
#         else:
#             cluster_id = sys.argv[1]
#             with open("./metrics/metrics", 'w', encoding='utf-8') as f:
#                 print(get_metrics(cluster_id, start, finish), file=f)
#         with open("./metrics/metrics", 'r', encoding='utf-8') as f:
#             m = json.loads(f.read().replace("'", "\""))
#         score = analyze(m, t)
#
#         ce = boto3.client('ce')
#         response = ce.get_cost_and_usage(
#             TimePeriod={
#                 'Start': time.strftime("%Y-%m-%d", time.localtime(start)),
#                 'End': time.strftime("%Y-%m-%d", time.localtime(finish + 86400))
#             },
#             Granularity='DAILY',
#             Metrics=[
#                 'UNBLENDED_COST',
#             ]
#         )
#         costs = []
#         for entry in response['ResultsByTime']:
#             record = entry['Total']['UnblendedCost']
#             shown = False
#             for cost in costs:
#                 if cost['Unit'] == record['Unit']:
#                     cost['Amount'] += record['Amount']
#                     shown = True
#                     break
#             if not shown:
#                 costs.append(record)
#         logging.info("--------------------------------")
#         logging.info("Total cost:")
#         for cost in costs:
#             logging.info(str(cost['Amount']) + " " + str(cost['Unit']))
#         logging.info("--------------------------------")
#         logging.info("Benchmark finished.")
#         logging.info("--------------------------------")
#     else:
#         logging.error("Invalid arguments. Please give cluster ID, start time and finish time.")
#         logging.info("If you have collected metrics from CWAgent, please set cluster ID to -1.")
