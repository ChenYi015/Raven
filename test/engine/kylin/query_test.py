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
from benchmark.cloud.aws.kylin import KylinCluster
from benchmark.core.query import Query
from benchmark.engine.kylin import KylinEngine

if __name__ == '__main__':
    import configs

    config = configs.CLOUD_CONFIG['Properties']
    aws = AmazonWebService(
        region=config['Region'],
        ec2_key_name=config['Ec2KeyName']
    )

    kylin_cluster = KylinCluster(
        aws=aws,
        master_instance_type=config['MasterInstanceType'],
        worker_instance_type=config['CoreInstanceType'],
        worker_num=config['CoreInstanceCount'],
    )
    kylin_cluster.launch()

    kylin_engine = KylinEngine(
        host=kylin_cluster.master.public_ip,
        port=7070
    )
    query1 = Query(
        database='ssb',
        sql="""select sum(v_revenue) as revenue
from p_lineorder
left join dates on lo_orderdate = d_datekey
where d_year = 1993
and lo_discount between 1 and 3
and lo_quantity < 25"""
    )

    query2 = Query(
        database='ssb',
        sql="""SELECT SUM(LO_EXTENDEDPRICE * LO_DISCOUNT) AS REVENUE
FROM LINEORDER, DATES
WHERE LO_ORDERDATE = D_DATEKEY
AND D_YEAR = 1993
AND LO_DISCOUNT BETWEEN 1 AND 3
AND LO_QUANTITY < 25"""
    )
    response = kylin_engine.execute_query(query2)
