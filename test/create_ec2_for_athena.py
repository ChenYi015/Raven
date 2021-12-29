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

from benchmark.cloud.provider import Provider

import configs
<<<<<<< HEAD
from benchmark.cloud.provider import Provider
=======
>>>>>>> c6e57f152b6cf3642e1037d16220c2d7462bcd36

if __name__ == '__main__':
    # AWS Cloud Provider
    aws = Provider(configs.PROVIDER_CONFIG)
    stack_name = 'Raven-Stack-for-Athena'
    with open(os.path.join(os.environ['RAVEN_HOME'], 'configs', 'providers', 'aws', 'athena-cloudformation.yaml'),
              encoding='utf-8') as file:
        template_body = file.read()
    aws.create_stack(stack_name=stack_name, template_body=template_body, tags=configs.TAGS)
