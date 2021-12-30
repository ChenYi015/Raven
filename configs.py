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

import logging.config
import logging.handlers
import os

import yaml


# Logging

class RavenTimedRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):

    def __init__(self, filename, when='h', interval=1, backupCount=0, encoding=None, delay=False, utc=False,
                 atTime=None):
        filename = os.path.join(os.environ['RAVEN_HOME'], *filename.split('/'))
        super().__init__(filename, when, interval, backupCount, encoding, delay, utc)


class RavenFileHandler(logging.FileHandler):

    def __init__(self, filename, mode='a', encoding=None, delay=False):
        _filename = os.path.join(os.environ['RAVEN_HOME'], *filename.split('/'))
        super().__init__(_filename, mode, encoding, delay)


with open(os.path.join(os.environ['RAVEN_HOME'], 'config', 'logging.yaml'), encoding='utf-8') as _:
    logging_config = yaml.load(_, Loader=yaml.FullLoader)
    logging.config.dictConfig(logging_config)

ROOT_LOGGER = logging.getLogger('root')
HOOK_LOGGER = logging.getLogger('hookLogger')
CONSOLE_LOGGER = logging.getLogger('consoleLogger')
GENERATE_LOGGER = logging.getLogger('generateLogger')
EXECUTE_LOGGER = logging.getLogger('executeLogger')
COLLECT_LOGGER = logging.getLogger('collectLogger')


GITHUB_REPO_URL = 'https://github.com/ChenYi015/Raven.git'


# Raven
with open(os.path.join(os.environ['RAVEN_HOME'], 'config', 'raven.yaml'), encoding='utf-8') as file:
    config = yaml.load(file, yaml.FullLoader)

CLOUD_CONFIG = config['Cloud']

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

with open(os.path.join(os.environ['RAVEN_HOME'], 'config', 'engine', 'athena', 'athena.yaml'), encoding='utf-8') as file:
    ATHENA_CONFIG = yaml.load(file, Loader=yaml.FullLoader)

if __name__ == '__main__':
    pass
