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

import yaml

from benchmark.engines.kylin4.constants import KylinFile, KylinConfig
from benchmark.providers.aws.provider import Provider

if __name__ == '__main__':
    with open(os.path.join(os.environ['RAVEN_HOME'], 'benchmark', 'engines', 'kylin4', 'configs', 'kylin.yaml'),
              encoding='utf-8') as stream:
        kylin_config = yaml.load(stream, Loader=yaml.FullLoader)

    with open(os.path.join(os.environ['RAVEN_HOME'], 'configs', 'raven.yaml'), encoding='utf-8') as stream:
        raven_config = yaml.load(stream, Loader=yaml.FullLoader)
    provider = Provider(raven_config['Provider'])

    # Create Kylin Constants Stack
    with open(KylinFile.CONSTANTS_YAML, encoding='utf-8') as file:
        template_body = file.read()
    provider.create_stack(
        stack_name=kylin_config[KylinConfig.CONSTANTS_STACK],
        template_body=template_body
    )

    # Create Kylin VPC Stack
    with open(KylinFile.VPC_YAML, encoding='utf-8') as file:
        template_body = file.read()
    provider.create_stack(
        stack_name=kylin_config[KylinConfig.VPC_STACK],
        template_body=template_body
    )

    # Create Kylin Distribution Stack
    with open(KylinFile.DISTRIBUTION_YAML, encoding='utf-8') as file:
        template_body = file.read()
    provider.create_stack(
        stack_name=kylin_config[KylinConfig.DISTRIBUTION_STACK],
        template_body=template_body,
    )

    # Create Kylin Master Stack
    with open(KylinFile.MASTER_YAML, encoding='utf-8') as file:
        template_body = file.read()
    provider.create_stack(
        stack_name=kylin_config[KylinConfig.MASTER_STACK],
        template_body=template_body,
    )

    # Create Kylin Slave Stack
    with open(KylinFile.SLAVE_YAML, encoding='utf-8') as file:
        template_body = file.read()
    provider.create_stack(
        stack_name=kylin_config[KylinConfig.SLAVE_STACK],
        template_body=template_body,
    )
