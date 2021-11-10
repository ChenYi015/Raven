import logging

from .engine import Engine

logger = logging.getLogger(__name__)


def hook(engine: Engine):
    logger.info(f'Athena: no op in {__file__}')
