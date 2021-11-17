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

GITHUB_REPO_URL = 'https://github.com/ChenYi015/Raven.git'

with open(os.path.join(os.environ['RAVEN_HOME'], 'configs', 'raven.yaml'), encoding='utf-8') as file:
    config = yaml.load(file, yaml.FullLoader)

PROVIDER_CONFIG = config['Provider']


ENGINE_CONFIG = config['Engine']


TESTPLAN_CONFIG = config['Testplan']
WORKLOAD_CONFIG = config['Workload']
Metrics = config['Metrics']
Scores = config['Scores']

TAGS = [
    {
        'Key': 'Project',
        'Value': 'Raven'
    },
    {
        'Key': 'Owner',
        'Value': 'ChenYi'
    }
]
