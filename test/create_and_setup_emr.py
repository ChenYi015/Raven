from benchmark.cloud.provider import Provider

import configs
<<<<<<< HEAD
from benchmark.cloud.provider import Provider
=======
>>>>>>> c6e57f152b6cf3642e1037d16220c2d7462bcd36

if __name__ == '__main__':
    # AWS Cloud Provider
    aws = Provider(configs.PROVIDER_CONFIG)

    # Create stack for SparkSQL
    stack_name, cluster_id = aws.create_emr_stack_for_engine(engine='presto', tags=configs.TAGS, install_cwa=False)
