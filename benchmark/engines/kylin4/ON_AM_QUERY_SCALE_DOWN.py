import logging

from .engine import Engine

logger = logging.getLogger(__name__)


def hook(engine: Engine):
    logger.info(f"Query scale down, down the workers from cluster {engine.server_mode} "
                f"for {'ec2' if engine.is_ec2_cluster else 'emr'}")
    engine.scale_down_workers()
