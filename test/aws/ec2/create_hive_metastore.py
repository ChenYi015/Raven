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


import configs
from benchmark.cloud.aws.aws import AmazonWebService

config = configs.CLOUD_CONFIG['Properties']
aws = AmazonWebService(region=config['Region'], ec2_key_name=config['Ec2KeyName'])

aws.create_hive_metastore(ec2_key_name='key_raven')

# aws.terminate_hive_metastore()
