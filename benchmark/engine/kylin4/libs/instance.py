from enum import Enum

from benchmark.engine.kylin4.libs import lightning


class ServerMode(Enum):
    ALL = 'all'
    JOB = 'job'
    QUERY = 'query'


class KylinInstance:

    def __init__(self, **kwargs):
        self._host = kwargs['host']
        self._port = kwargs['port']
        self._home = kwargs['home']
        self._mode = kwargs['mode']
        self.client = lightning.connect(host=self._host, port=self._port)
