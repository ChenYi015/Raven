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


class KylinFile:
    CONSTANTS_YAML = os.path.join(os.environ['RAVEN_HOME'], 'benchmark', 'engines', 'kylin4', 'configs',
                                  'kylin4-constants-stack.yaml')

    VPC_YAML = os.path.join(os.environ['RAVEN_HOME'], 'benchmark', 'engines', 'kylin4', 'configs',
                            'kylin4-vpc-stack.yaml')
    DISTRIBUTION_YAML = os.path.join(os.environ['RAVEN_HOME'], 'benchmark', 'engines', 'kylin4', 'configs',
                                     'kylin4-distribution-stack.yaml')
    RAVEN_CLIENT_YAML = os.path.join(os.environ['RAVEN_HOME'], 'benchmark', 'engines', 'kylin4', 'configs',
                                     'raven-client.yaml')
    # resource_manager yaml and slave yaml already contain the kylin4 and other needed services installed and run
    MASTER_YAML = os.path.join(os.environ['RAVEN_HOME'], 'benchmark', 'engines', 'kylin4', 'configs',
                               'kylin4-resource_manager-stack.yaml')
    SLAVE_YAML = os.path.join(os.environ['RAVEN_HOME'], 'benchmark', 'engines', 'kylin4', 'configs',
                              'kylin4-slave-stack.yaml')
    SLAVE_SCALE_YAML = os.path.join(os.environ['RAVEN_HOME'], 'benchmark', 'engines', 'kylin4', 'configs',
                                    'ec2-cluster-slave-template.yaml')

    EMR_FOR_KYLIN4_YAML = os.path.join(os.environ['RAVEN_HOME'], 'benchmark', 'engines', 'kylin4', 'configs',
                                       'emr-5.33-for-kylin4.yaml')
    KYLIN4_ON_EMR_YAML = os.path.join(os.environ['RAVEN_HOME'], 'benchmark', 'engines', 'kylin4', 'configs',
                                      'kylin4-on-emr-5.33.yaml')


class KylinMode:
    ALL = 'all'
    JOB = 'job'
    QUERY = 'query'


class KylinConfig:
    # DEBUG params
    CLOUD_ADDR = 'CLOUD_ADDR'

    # Deploy params
    DEPLOY_KYLIN_VERSION = 'DEPLOY_KYLIN_VERSION'
    DEPLOY_PLATFORM = 'DEPLOY_PLATFORM'

    # Ready Raven Client
    RAVEN_CLIENT_NEEDED = 'RAVEN_CLIENT_NEEDED'

    # Stack Names
    CONSTANTS_STACK = 'CONSTANTS_STACK'
    VPC_STACK = 'VPC_STACK'
    DISTRIBUTION_STACK = 'DISTRIBUTION_STACK'
    MASTER_STACK = 'MASTER_STACK'
    SLAVE_STACK = 'SLAVE_STACK'
    EMR_FOR_KYLIN4_STACK = 'EMR_FOR_KYLIN4_STACK'
    EMR_FOR_KYLIN3_STACK = 'EMR_FOR_KYLIN3_STACK'
    KYLIN4_STEP_ON_EMR_STACK = 'KYLIN4_STEP_ON_EMR_STACK'
    KYLIN3_STEP_ON_EMR_STACK = 'KYLIN3_STEP_ON_EMR_STACK'
    SLAVE_SCALE_WORKER = 'SLAVE_SCALE_{}_STACK'
    RAVEN_CLIENT_STACK = 'RAVEN_CLIENT_STACK'

    # Params
    EMR_FOR_KYLIN4_PARAMS = 'EMR_FOR_KYLIN4_PARAMS'
    EC2_DISTRIBUTION_PARAMS = 'EC2_DISTRIBUTION_PARAMS'
    EC2_MASTER_PARAMS = 'EC2_MASTER_PARAMS'
    EC2_SLAVE_PARAMS = 'EC2_SLAVE_PARAMS'
    KYLIN4_STEP_ON_EMR_PARAMS = 'KYLIN4_STEP_ON_EMR_PARAMS'
    EC2_SCALE_SLAVE_PARAMS = 'EC2_SCALE_SLAVE_PARAMS'
    EC2_RAVEN_CLIENT_PARAMS = 'EC2_RAVEN_CLIENT_PARAMS'


class StackStatus:
    CREATE_FAILED = 'CREATE_FAILED'
    ROLLBACK_IN_PROGRESS = 'ROLLBACK_IN_PROGRESS'
    ROLLBACK_FAILED = 'ROLLBACK_FAILED'
    ROLLBACK_COMPLETE = 'ROLLBACK_COMPLETE'
