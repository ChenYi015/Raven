# Copyright 2021 Raven Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


class EngineName:
    HIVE = 'HIVE'
    SPARK_SQL = 'SPARK_SQL'
    PRESTO = 'PRESTO'
    KYLIN4 = 'KYLIN4'
    ATHENA = 'ATHENA'


class EngineManager:

    @staticmethod
    def get_engine(engine_name: str, **kwargs):
        engine_name = engine_name.upper()
        if engine_name == EngineName.HIVE:
            from benchmark.engine.hive import HiveEngine
            return HiveEngine(**kwargs)
        elif engine_name == EngineName.SPARK_SQL:
            from benchmark.engine.spark import SparkSqlEngine
            return SparkSqlEngine(**kwargs)
        elif engine_name == EngineName.PRESTO:
            from benchmark.engine.presto import PrestoEngine
            return PrestoEngine(**kwargs)
        elif engine_name == EngineName.SPARK_SQL:
            from benchmark.engine.kylin4.engine import Engine
            return Engine(**kwargs)
        elif engine_name == EngineName.ATHENA:
            from benchmark.engine.athena import AthenaEngine
            return AthenaEngine(**kwargs)
        else:
            raise ValueError(f'Unsupported engine: {engine_name}')
