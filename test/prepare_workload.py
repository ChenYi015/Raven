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
import os

import yaml
from pyhive import hive


def prepare_workload_to_hive(config: dict):
    logging.info(f"Start to prepare workload {config['Name']}...")

    # connect hive
    cursor = hive.connect('localhost').cursor()

    # create database
    cursor.execute_queries(config['Database']['Create'])

    # create table and load data to table
    cursor.execute_queries(f"use {config['Database']['Name']}")
    for table_config in config['Tables']:
        cursor.execute_queries(table_config['Create'])
        cursor.execute_queries(table_config['Load'])

    logging.info(f"Finish preparing workload {config['Name']}.")


if __name__ == '__main__':
    # prepare TPC-H workload
    with open(os.path.join('configs', 'workloads', 'tpch.yaml'), encoding='utf-8') as file:
        workload_config = yaml.load(file, yaml.FullLoader)
    prepare_workload_to_hive(workload_config)

    # prepare TPC-DS workload
    with open(os.path.join('configs', 'workloads', 'workload.yaml'), encoding='utf-8') as file:
        workload_config = yaml.load(file, yaml.FullLoader)
    prepare_workload_to_hive(workload_config)

    # prepare SSB workload
    with open(os.path.join('configs', 'workloads', 'workload.yaml'), encoding='utf-8') as file:
        workload_config = yaml.load(file, yaml.FullLoader)
    prepare_workload_to_hive(workload_config)
