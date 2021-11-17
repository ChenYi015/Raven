import logging.config
import os

import yaml

import benchmark.config
from benchmark.providers.aws.provider import Provider

if __name__ == '__main__':
    # Logging
    with open(os.path.join(os.environ['RAVEN_HOME'], 'configs', 'logging.yaml'), encoding='utf-8') as _:
        logging_config = yaml.load(_, Loader=yaml.FullLoader)
        logging.config.dictConfig(logging_config)

    # AWS Cloud Provider
    aws = Provider(benchmark.config.PROVIDER_CONFIG)

    # Create stack for SparkSQL
    stack_name, cluster_id = aws.create_emr_stack_for_engine(engine='spark-sql', tags=benchmark.config.TAGS)

    aws.setup_emr_with_commands(
        cluster_id=cluster_id,
        commands=[
            'sudo yum install -y amazon-cloudwatch-agent',
            'sudo mkdir -p /usr/share/collectd',
            'sudo touch /usr/share/collectd/types.db',
            'aws s3 cp s3://olapstorage/configs/amazon-cloudwatch-agent.json /home/hadoop',
            'sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:/home/hadoop/amazon-cloudwatch-agent.json',
            'sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -m ec2 -a status'
        ]
    )

    aws.setup_emr_master_with_commands(
        cluster_id=cluster_id,
        commands=[
            'sudo yum install -y git',
            f'git clone {benchmark.config.GITHUB_REPO_URL} /home/hadoop/Raven',
            'cd /home/hadoop/Raven; git checkout dev; chmod u+x bin/setup.sh; bin/setup.sh'
        ]
    )
