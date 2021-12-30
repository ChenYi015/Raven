import os

import yaml

from config.engine.kylin.constants import KylinConfig
from config.engine.kylin.libs import KylinInstance

if __name__ == '__main__':
    cloud_addr = '18.140.64.108'

    with open(os.path.join(os.environ['RAVEN_HOME'], 'benchmark', 'engines', 'kylin4', 'configs', 'kylin.yaml'),
              encoding='utf-8') as stream:
        kylin_config = yaml.load(stream, Loader=yaml.FullLoader)

    kylin_mode = kylin_config[KylinConfig.EC2_MASTER_PARAMS]['Ec2KylinMode']
    # launch kylin
    kylin_instance = KylinInstance(host=cloud_addr, port='7070', home=None, mode=kylin_mode)
    assert kylin_instance.client.await_kylin_start(
        check_action=kylin_instance.client.check_login_state,
        timeout=10,
        check_times=3
    )
