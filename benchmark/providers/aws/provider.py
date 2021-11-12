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


import boto3


class Provider:

    def __init__(self, config: dict):
        self._name = 'Amazon Web Service'
        self._session = boto3.session.Session(config['Session']) if 'Session' is not None else boto3.session.Session()

    @property
    def name(self):
        return self._name

    # AWS Cost Explorer
    def get_cost_and_usage(self, ):
        pass


if __name__ == '__main__':
    config = {}
    provider = Provider(config)
