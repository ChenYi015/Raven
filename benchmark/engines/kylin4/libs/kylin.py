from benchmark.engines.kylin4.aws import AWS
from benchmark.engines.kylin4.constants import KylinConfig
from benchmark.engines.kylin4.libs.instance import KylinInstance


def launch_aws_kylin(config) -> KylinInstance:
    cloud_addr = 'localhost'
    # cloud_addr = get_cloud_addr(config)
    kylin_mode = config[KylinConfig.EC2_MASTER_PARAMS]['Ec2KylinMode']
    # launch kylin
    kylin_instance = KylinInstance(host=cloud_addr, port='7070', home=None, mode=kylin_mode)
    assert kylin_instance.client.await_kylin_start(
        check_action=kylin_instance.client.check_login_state,
        timeout=1800,
        check_times=3
    )
    return kylin_instance


def destroy_aws_kylin(config):
    AWS.destroy_aws_cloud(config)


def scale_aws_worker(worker_num: int, config):
    assert get_cloud_addr(config), 'Master node must be ready.'
    AWS.scale_worker_to_ec2(worker_num, config)


def scale_down_aws_worker(worker_num: int, config):
    AWS.scale_down_worker(worker_num, config)


def get_cloud_addr(config) -> str:
    """
    Retrieve Kylin and Spark master ip.
    :param config: config from global yaml
    :return: cloud_addr which from the master public ip or private ip
    """
    # launch aws cluster
    if config[KylinConfig.CLOUD_ADDR.value] is None:
        cloud_addr = AWS.aws_cloud(config)
    else:
        cloud_addr = config[KylinConfig.CLOUD_ADDR.value]
    # make sure that cloud addr always exists
    assert cloud_addr is not None, 'cloud address is None, please check.'
    return cloud_addr
