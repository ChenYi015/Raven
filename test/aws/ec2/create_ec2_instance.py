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

from benchmark.cloud.aws.aws import AmazonWebService, Ec2Instance

if __name__ == '__main__':
    import configs

    config = configs.CLOUD_CONFIG['Properties']
    aws = AmazonWebService(
        region=config['Region'],
        ec2_key_name=config['Ec2KeyName']
    )
    with open(os.path.join(os.environ['RAVEN_HOME'], 'config', 'cloud', 'aws', 'ec2-cloudformation-template.yaml'),
              encoding='utf-8') as file:
        template = file.read()
    ec2_instance = Ec2Instance(name='Test Instance', aws=aws, stack_name='EC2-Test-Stack', template=template,
                               ec2_instance_type='m5.large')
    ec2_instance.launch()
    # ec2_instance.install_cloudwatch_agent()
    ec2_instance.get_metrics()
    ec2_instance.get_metrics()
    ec2_instance.terminate()
