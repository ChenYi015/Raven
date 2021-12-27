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
from benchmark.cloud.aws.provider import Provider

if __name__ == '__main__':
    aws = Provider(configs.PROVIDER_CONFIG)

    # Test S3

    # Test S3 list buckets
    # print(aws.list_buckets())

    # Test S3 upload file
    file_name = 'test.txt'
    bucket_name = 'chenyi-ap-southeast-1'
    # with open(filename, mode='w', encoding='utf-8') as file:
    #     file.write('This is some text.')
    # aws.upload_file(
    #     file_name=file_name,
    #     bucket=bucket_name
    # )

    # Test s3 download file
    aws.download_file(
        bucket_name=bucket_name,
        object_name=file_name,
        file_name=file_name
    )
