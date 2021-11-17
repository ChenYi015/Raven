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

if __name__ == '__main__':
    # 使用 AWS Glue 完成数据 ETL 工作

    # Example: create and run a job

    # 1. Create an instance of the AWS Glue client
    glue = boto3.client(
        service_name='glue',
        region_name='ap-southeast-1',
        endpoint_url='https://ap-southeast-1.amazonaws.com'
    )

    # 2. Create a job
    job = glue.create_job(
        Name='sample',
        Role='Glue_DefaultRole',
        Command={
            'Name': 'glueetl',
            'ScriptLocation': 's3://my_script_bucket/scripts/my_etl_script.py'
        }
    )

    # 3. Start a new run of the job
    jobRun = glue.start_job_run(JobName=job['Name'])

    # 4. Get the job status
    status = glue.get_job_run(JobName=job['Name'], RunId=jobRun['JobRunId'])

    # 5. Print the current state of the job run
    print(status['JobRun']['JobRunState'])
