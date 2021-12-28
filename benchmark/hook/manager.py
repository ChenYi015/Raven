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

import logging

from benchmark.core.engine import Engine


class HookName:
    ON_AM_QUERY_START = 'ON_AM_QUERY_START'
    ON_AM_QUERY_FINISH = 'ON_AM_QUERY_FINISH'
    ON_ETL_START = 'ON_ETL_START'
    ON_ETL_FINISH = 'ON_ETL_FINISH'
    ON_PM_QUERY_START = 'ON_PM_QUERY_START'
    ON_PM_QUERY_FINISH = 'ON_PM_QUERY_FINISH'
    ON_QUERY_START = 'ON_QUERY_START'
    ON_QUERY_START_30_MINUTES_COUNTDOWN = 'ON_QUERY_START_30_MINUTES_COUNTDOWN'


def on_am_query_start(engine: Engine):
    pass


def on_am_query_finish(engine: Engine):
    pass


def on_etl_start(engine: Engine):
    pass


def on_etl_finish(engine: Engine):
    pass


def on_pm_query_start(engine: Engine):
    pass


def on_pm_query_finish(engine: Engine):
    pass


def on_query_start(engine: Engine):
    logging.info('Query start...')


def on_query_start_30_minutes_countdown(engine: Engine):
    pass


class HookManager:

    @staticmethod
    def get_hook(event_name: str):
        event_name = event_name.upper()
        if event_name == HookName.ON_AM_QUERY_START:
            return on_am_query_start
        elif event_name == HookName.ON_AM_QUERY_FINISH:
            return on_am_query_finish
        elif event_name == HookName.ON_ETL_START:
            return on_etl_start
        elif event_name == HookName.ON_ETL_FINISH:
            return on_etl_finish
        elif event_name == HookName.ON_PM_QUERY_START:
            return on_pm_query_start
        elif event_name == HookName.ON_PM_QUERY_FINISH:
            return on_pm_query_finish
        elif event_name == HookName.ON_QUERY_START:
            return on_query_start
        elif event_name == HookName.ON_QUERY_START_30_MINUTES_COUNTDOWN:
            return on_query_start_30_minutes_countdown
        else:
            raise ValueError(f'Unsupported event name: {event_name}.')
