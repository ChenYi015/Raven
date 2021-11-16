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

from pprint import pprint

import boto3
import botocore.exceptions

if __name__ == '__main__':
    client = boto3.client('emr')
    try:
        response = client.add_job_flow_steps(
            JobFlowId='j-2KW4G4YZ7ZSJ2',
            Steps=[
                {
                    'Name': 'step1',
                    'ActionOnFailure': 'CANCEL_AND_WAIT',
                    'HadoopJarStep': {
                        'Jar': 's3://ap-southeast-1.elasticmapreduce/libs/script-runner/script-runner.jar',
                        'Args': [
                            's3://olapstorage/scripts/emr_bootstrap.sh',
                        ]
                    }
                },
            ]
        )
    except botocore.exceptions.ClientError as error:
        pprint(error.response)
