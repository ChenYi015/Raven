import logging
import time

from .constant.config import Config
from .engine import Engine

logger = logging.getLogger(__name__)


def hook(engine: Engine):
    logger.info(f"check or launch {'ec2' if engine.is_ec2_cluster else 'emr'} cluster for Query ...")
    if engine.is_ec2_cluster:
        # set server mode
        engine.server_mode = 'query'
        engine.config[Config.EC2_MASTER_PARAMS.value]['Ec2KylinMode'] = engine.server_mode
    engine.launch_cluster()
    # FIXME: hard code time for ready
    time.sleep(600)
