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
from benchmark.cloud.aws.presto import PrestoCluster
from benchmark.core.query import Query
from benchmark.engine.presto import PrestoEngine

if __name__ == '__main__':
    import configs

    config = configs.CLOUD_CONFIG['Properties']
    aws = AmazonWebService(region=config['Region'], ec2_key_name=config['Ec2KeyName'])

    presto_cluster = PrestoCluster(aws=aws, master_instance_type='t2.small', worker_instance_type='t2.small', worker_num=1)
    presto_cluster.launch()

    presto_engine = PrestoEngine(
        host=presto_cluster.coordinator.public_ip,
    )

    query = Query(database='ssb_1g', sql='SELECT * FROM CUSTOMER LIMIT 5')
    presto_engine.execute_query(query)

    presto_cluster.terminate()
