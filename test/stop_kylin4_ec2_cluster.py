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

import configs
from config.engine.kylin.constants import KylinConfig
<<<<<<< HEAD
from benchmark.cloud.provider import Provider
=======
>>>>>>> c6e57f152b6cf3642e1037d16220c2d7462bcd36

if __name__ == '__main__':
    # AWS Cloud Provider
    aws = Provider(configs.PROVIDER_CONFIG)

    with open(os.path.join(os.environ['RAVEN_HOME'], 'benchmark', 'engines', 'kylin4', 'configs', 'kylin.yaml'),
              encoding='utf-8') as stream:
        kylin_config = yaml.load(stream, Loader=yaml.FullLoader)

    # Delete Kylin Constants Stack
    aws.delete_stack(stack_name=kylin_config[KylinConfig.CONSTANTS_STACK])

    # Delete Kylin VPC Stack
    aws.delete_stack(stack_name=kylin_config[KylinConfig.VPC_STACK])

    # Delete Kylin Distribution Stack
    aws.delete_stack(stack_name=kylin_config[KylinConfig.DISTRIBUTION_STACK])

    # Delete Kylin Master Stack
    aws.delete_stack(stack_name=kylin_config[KylinConfig.MASTER_STACK])

    # Delete Kylin Slave Stack
    aws.delete_stack(stack_name=kylin_config[KylinConfig.SLAVE_STACK])
