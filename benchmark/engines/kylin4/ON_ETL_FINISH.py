import logging

from .engine import Engine

logger = logging.getLogger(__name__)


def hook(engine: Engine):
    logger.info(f"ETL finished, destroy cluster {engine.server_mode} "
                f"for {'ec2' if engine.is_ec2_cluster else 'emr'}")
    engine.destroy_cluster()
