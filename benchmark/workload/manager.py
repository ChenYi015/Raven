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

import yaml

from benchmark.core.workload import TimelineWorkload
from benchmark.workload.ssb import SsbLoopWorkload, SsbQpsWorkload, SsbKylinLoopWorkload, SsbKylinQpsWorkload, \
    SSB_QUERIES
from benchmark.workload.tpcds import TpcdsLoopWorkload, TpcdsQpsWorkload
from benchmark.workload.tpch import TpchLoopWorkload, TpchQpsWorkload


class WorkloadName:
    TPCH = 'TPC-H'
    TPCDS = 'TPC-DS'
    SSB = 'SSB'
    SSB_KYLIN4 = 'SSB_KYLIN4'


class WorkloadType:
    LOOP = 'LOOP'
    QPS = 'QPS'
    TIMELINE = 'TIMELINE'


class WorkloadManager:

    @staticmethod
    def get_workload(workload_name: str, workload_type: str):
        workload_name, workload_type = workload_name.upper(), workload_type.upper()
        if workload_name == WorkloadName.TPCH:
            return WorkloadManager.get_tpch_workload(workload_type=workload_type)
        elif workload_name == WorkloadName.TPCDS:
            return WorkloadManager.get_tpcds_workload(workload_type=workload_type)
        elif workload_name == WorkloadName.SSB:
            return WorkloadManager.get_ssb_workload(workload_type=workload_type)
        elif workload_name == WorkloadName.SSB_KYLIN4:
            return WorkloadManager.get_ssb_kylin_workload(workload_type=workload_type)
        elif workload_type == WorkloadType.TIMELINE:
            return WorkloadManager.get_timeline_workload()
        else:
            raise ValueError('Unsupported workload name.')

    @staticmethod
    def get_tpch_workload(workload_type: str):
        if workload_type == WorkloadType.LOOP:
            return TpchLoopWorkload()
        elif workload_type == WorkloadType.QPS:
            return TpchQpsWorkload()
        else:
            raise ValueError('Unsupported workload type.')

    @staticmethod
    def get_tpcds_workload(workload_type: str):
        if workload_type == WorkloadType.LOOP:
            return TpcdsLoopWorkload()
        elif workload_type == WorkloadType.QPS:
            return TpcdsQpsWorkload()
        else:
            raise ValueError('Unsupported workload type.')

    @staticmethod
    def get_ssb_workload(workload_type: str):
        if workload_type == WorkloadType.LOOP:
            return SsbLoopWorkload()
        elif workload_type == WorkloadType.QPS:
            return SsbQpsWorkload()
        else:
            raise ValueError('Unsupported workload type.')

    @staticmethod
    def get_ssb_kylin_workload(workload_type: str):
        if workload_type == WorkloadType.LOOP:
            return SsbKylinLoopWorkload()
        elif workload_type == WorkloadType.QPS:
            return SsbKylinQpsWorkload()
        else:
            raise ValueError('Unsupported workload type.')

    @staticmethod
    def get_timeline_workload():
        with open(os.path.join(os.environ['RAVEN_HOME'], 'config', 'workload', 'kylin-custom.yaml')) as file:
            config = yaml.load(file, Loader=yaml.FullLoader)
            return TimelineWorkload(name=config['Name'], description='Kylin custom workload', queries=SSB_QUERIES,
                                    timeline=config['Timeline'])
