import logging.config
import os
import random
import string

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
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    stack_name = f'EMR-Raven-Stack-{random_suffix}'
    filename = 'emr-cloudformation-for-spark-sql.yaml'
    aws.create_stack(stack_name=stack_name, filename=filename)
