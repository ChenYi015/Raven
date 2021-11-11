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

    # TotalTime
    TotalElapsedTime = 'total_elapsed_time'

    # ReactionTime
    ReactionTime = 'reaction_time'
    AverageReactionTime = 'average_reaction_time'
    MinReactionTime = 'min_reaction_time'
    MedianReactionTime = 'median_reaction_time'
    MaxReactionTime = 'max_reaction_time'
    PercentileReactionTime = 'percentile_reaction_time'

    # Latency
    Latency = 'latency'
    AverageLatency = 'average_latency'
    MedianLatency = 'median_latency'
    MinLatency = 'min_latency'
    MaxLatency = 'max_latency'
    PercentileLatency = 'percentile_latency'

    # ResponseTime
    ResponseTime = 'response_time'
    AverageResponseTime = 'average_response_time'
    MedianResponseTime = 'median_response_time'
    MinResponseTime = 'min_response_time'
    MaxResponseTime = 'max_response_time'
    PercentileResponseTime = 'percentile_response_time'

    # Cost
    TotalCost = 'total_cost'
    PreComputingCost = 'pre_computing_cost'
    QueryCost = 'query_cost'

    # CPU Utilization
    AverageCPUUtilization = 'average_cpu_utilization'

    # Memory Utilization
    AverageMemoryUtilization = 'average_memory_utilization'

    # Disk Utilization
    AverageDiskUtilization = 'average_disk_utilization'
