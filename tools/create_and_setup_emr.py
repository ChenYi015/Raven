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
    cluster_id = aws.create_emr_for_engine(engine='spark-sql')
    aws.setup_emr_with_commands(
        cluster_id=cluster_id,
        commands=[
            'sudo install -y git',
            f'git clone {benchmark.config.GITHUB_REPO_URL} /home/hadoop/Raven',
            'cd /home/hadoop/Raven && git checkout dev',
            'sudo bash /home/hadoop/Raven/bin/setup.sh'
        ]
    )
