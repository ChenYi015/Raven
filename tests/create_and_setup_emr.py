import configs
from benchmark.providers.aws.provider import Provider

if __name__ == '__main__':
    # AWS Cloud Provider
    aws = Provider(configs.PROVIDER_CONFIG)

    # Create stack for SparkSQL
    stack_name, cluster_id = aws.create_emr_stack_for_engine(engine='presto', tags=configs.TAGS, install_cwa=False)
