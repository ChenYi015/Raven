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

from benchmark.cloud.aws.aws import AmazonWebService
from benchmark.cloud.aws.spark import SparkCluster

if __name__ == '__main__':
    import configs

    config = configs.CLOUD_CONFIG['Properties']
    aws = AmazonWebService(region=config['Region'], ec2_key_name=config['Ec2KeyName'])

    spark_cluster = SparkCluster(
        aws=aws,
        master_instance_type=config['MasterInstanceType'],
        worker_instance_type=config['CoreInstanceType'],
        worker_num=config['CoreInstanceCount']
    )
    spark_cluster.launch()
    spark_cluster.collect_cluster_info()
    spark_cluster.install_cloud_watch_agent()
    spark_cluster.collect_metrics()
    spark_cluster.terminate()
