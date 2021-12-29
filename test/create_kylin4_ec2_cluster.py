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
import json
import os

import yaml
from benchmark.cloud.provider import Provider

import configs
from benchmark.engine.kylin4.constants import KylinFile, KylinConfig
<<<<<<< HEAD
from benchmark.cloud.provider import Provider
=======
>>>>>>> c6e57f152b6cf3642e1037d16220c2d7462bcd36
from tools import ssh_exec_commands

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
        template_body=template_body
    )

    # Create Kylin Master Stack
    with open(KylinFile.MASTER_YAML, encoding='utf-8') as file:
        template_body = file.read()
    provider.create_stack(
        stack_name=kylin_config[KylinConfig.MASTER_STACK],
        template_body=template_body
    )

    # Create Kylin Slave Stack
    with open(KylinFile.SLAVE_YAML, encoding='utf-8') as file:
        template_body = file.read()
    provider.create_stack(
        stack_name=kylin_config[KylinConfig.SLAVE_STACK],
        template_body=template_body
    )

    # Install AWS CloudWatch Agent
    key_name = configs.PROVIDER_CONFIG['Properties']['KeyName']
    # commands = []
    commands = [
        'sudo yum install -y amazon-cloudwatch-agent',
        'sudo mkdir -p /usr/share/collectd',
        'sudo touch /usr/share/collectd/types.db',
        'aws s3 cp s3://olapstorage/configs/amazon-cloudwatch-agent.json /home/ec2-user',
        'sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:/home/ec2-user/amazon-cloudwatch-agent.json',
        'sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -m ec2 -a status'
    ]

    master_instance_id = provider.get_stack_output_by_key(stack_name='Kylin4-Master-Stack',
                                                          output_key='MasterInstanceId')
    master_public_ip = provider.get_stack_output_by_key(stack_name='Kylin4-Master-Stack',
                                                        output_key='MasterPublicIp')
    ssh_exec_commands(
        hostname=master_public_ip,
        key_name=key_name,
        username='ec2-user',
        commands=commands
    )
    ssh_exec_commands(
        hostname=master_public_ip,
        key_name=key_name,
        username='ec2-user',
        commands=[
            'sudo yum install -y git',
            f'git clone {configs.GITHUB_REPO_URL} /home/ec2-user/Raven',
            'cd /home/ec2-user/Raven && git checkout dev'
        ]
    )

    slaves = []
    for slave in [f'Slave{slave_id:02d}' for slave_id in range(1, 11)]:
        public_ip = provider.get_stack_output_by_key(stack_name='Kylin4-Slave-Stack',
                                                     output_key=f'{slave}Ec2InstancePublicIp')
        instance_id = provider.get_stack_output_by_key(stack_name='Kylin4-Slave-Stack',
                                                       output_key=f'{slave}Ec2InstanceId')
        if public_ip and instance_id:
            slaves.append(
                {
                    'InstanceId': instance_id,
                    'PublicIp': public_ip
                }
            )
            ssh_exec_commands(
                hostname=public_ip,
                key_name=key_name,
                username='ec2-user',
                commands=commands
            )

    # Write cluster info to file
    kylin4_cluster_info: dict = {
        'Master': {
            'InstanceId': master_instance_id,
            'PublicIp': master_public_ip
        },
        'Slaves': slaves
    }

    path = os.path.join(os.environ['RAVEN_HOME'], 'out', f'ec2_{master_instance_id}', 'cluster_info.json')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, mode='w') as file:
        json_str = json.dumps(kylin4_cluster_info, indent=2)
        file.write(json_str)
