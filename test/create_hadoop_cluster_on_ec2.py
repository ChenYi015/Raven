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

<<<<<<< HEAD
import os

import configs
from benchmark.cloud.provider import Provider
=======
from benchmark.cloud.aws import AmazonWebService
>>>>>>> c6e57f152b6cf3642e1037d16220c2d7462bcd36

if __name__ == '__main__':
    aws = AmazonWebService(region='ap-southeast-1')

    # aws.create_hadoop_ec2_cluster(ec2_key_name='key_raven', master_instance_type='t2.small',
    #                               worker_instance_type='t2.small', worker_num=1)

    aws.terminate_hadoop_ec2_cluster()
