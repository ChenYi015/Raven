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


class Metric:
    """指标相关的字符串常量."""

    # TotalTime
    TOTAL_ELAPSED_TIME = 'total_elapsed_time'

    # ReactionTime
    REACTION_TIME = 'reaction_time'
    AVERAGE_REACTION_TIME = 'average_reaction_time'
    MIN_REACTION_TIME = 'min_reaction_time'
    MEDIAN_REACTION_TIME = 'median_reaction_time'
    MAX_REACTION_TIME = 'max_reaction_time'
    PERCENTILE_REACTION_TIME = 'percentile_reaction_time'

    # Latency
    LATENCY = 'latency'
    AVERAGE_LATENCY = 'average_latency'
    MEDIAN_LATENCY = 'median_latency'
    MIN_LATENCY = 'min_latency'
    MAX_LATENCY = 'max_latency'
    PERCENTILE_LATENCY = 'percentile_latency'

    # ResponseTime
    RESPONSE_TIME = 'response_time'
    AVERAGE_RESPONSE_TIME = 'average_response_time'
    MEDIAN_RESPONSE_TIME = 'median_response_time'
    MIN_RESPONSE_TIME = 'min_response_time'
    MAX_RESPONSE_TIME = 'max_response_time'
    PERCENTILE_RESPONSE_TIME = 'percentile_response_time'

    # Cost
    TOTAL_COST = 'total_cost'
    PreComputingCost = 'pre_computing_cost'
    QueryCost = 'query_cost'

    # CPU Utilization
    AVERAGE_CPU_UTILIZATION = 'average_cpu_utilization'

    # Memory Utilization
    AVERAGE_MEMORY_UTILIZATION = 'average_memory_utilization'

    # Disk Utilization
    AVERAGE_DISK_UTILIZATION = 'average_disk_utilization'
