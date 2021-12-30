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

import os
import time

import boto3
import yaml

import configs
from benchmark.core.engine import Engine
from benchmark.core.query import Query, QueryStatus

logger = configs.EXECUTE_LOGGER


class AthenaEngine(Engine):

    def __init__(self, *, concurrency: int = 1, **kwargs):
        super().__init__(name='Athena', description='AWS Athena', concurrency=concurrency)
        self._region = kwargs['region']
        self._boto3_session = boto3.session.Session(region_name=self._region)

    def execute_query(self, query: Query) -> Query:
        query.status = QueryStatus.RUNNING
        logger.info(f'{self.name} engine is executing {query}.')
        try:
            athena_query = AthenaQuery(
                boto3_session=self._boto3_session,
                database=query.database,
                query=query.sql
            )
            athena_query.execute()
            result_data = athena_query.get_result()
            logger.info(f"Result rows: {len(result_data['ResultSet']['Rows'])}")
            query.status = QueryStatus.SUCCEEDED
            logger.info(f'{self.name} engine has finished executing {query}.')
        except Exception as error:
            query.status = QueryStatus.FAILED
            logger.error(f'{self.name} engines failed to execute {query}, an error has occurred: {error}')
        return query


class AthenaQuery:

    def __init__(self, database: str, query: str,
                 boto3_session: boto3.session.Session =None,
                 query_timeout: float = 60.0,
                 query_execution_id: str = ''):
        """
        :param query: SQL query.
        :param database: The name of database.
        :param boto3_session: AWS boto3 session.
        :param query_timeout: Query timeout limit.
        :param query_execution_id: The unique identifier of the query that ran as a result of this request.
        """
        with open(os.path.join(os.environ['RAVEN_HOME'], 'config', 'engine', 'athena', 'athena.yaml'),
                  encoding='utf-8') as file:
            self._config = yaml.load(file, Loader=yaml.FullLoader)
        self._boto3_session = boto3_session if boto3_session else boto3.session.Session()
        self._query = query
        self._database = database
        self._query_state = None
        self._state_change_reason = None
        self._stats_execution_time_in_millis = 0
        self._stats_data_scanned_in_bytes = 0
        self._query_execution_id = query_execution_id
        self._query_timeout = query_timeout
        self._output_location = self._config['QueryResultLocation']['Default']

    def __str__(self):
        return f'AthenaQuery({self._query}, Database: {self._database} Bucket: {self._output_location})'

    def _update_query_status(self):
        """
        Updates the internal query status of this object.
        NOTE: this fails silently, if the query has not yet been executed!
        :return:
        """

        # TODO: We should probably do some kind of rate limiting here...

        if self._query_execution_id is None:
            # No execution yet
            logger.debug("The query has not been executed!")
            return

        client = self._boto3_session.client('athena')
        response = client.get_query_execution(
            QueryExecutionId=self._query_execution_id
        )
        query_execution = response["QueryExecution"]
        self._query_state = query_execution["Status"]["State"]
        logger.debug("Current Query State for Execution ID: %s is: %s", self._query_execution_id, self._query_state)

        if "StateChangeReason" in query_execution["Status"]:
            self._state_change_reason = query_execution["Status"]["StateChangeReason"]

        if "EngineExecutionTimeInMillis" in query_execution["Statistics"]:
            self._stats_execution_time_in_millis = query_execution["Statistics"]["EngineExecutionTimeInMillis"]
        else:
            self._stats_execution_time_in_millis = 0

        if "DataScannedInBytes" in query_execution["Statistics"]:
            self._stats_data_scanned_in_bytes = query_execution["Statistics"]["DataScannedInBytes"]
        else:
            self._stats_data_scanned_in_bytes = 0

    def get_status_information(self):
        self._update_query_status()

        return {
            "QueryState": self._query_state,
            "ExecutionTimeInMillis": self._stats_execution_time_in_millis,
            "StateChangeReason": self._state_change_reason,
            "DataScannedInBytes": self._stats_data_scanned_in_bytes
        }

    def execute(self):
        client = self._boto3_session.client('athena')
        response = client.start_query_execution(
            QueryString=self._query,
            QueryExecutionContext={
                'Database': self._database
            },
            ResultConfiguration={
                'OutputLocation': self._output_location,
            }
        )

        logger.debug(f'Scheduled Athena-Query - Query Execution Id: {response["QueryExecutionId"]}')
        self._query_execution_id = response['QueryExecutionId']
        return response['QueryExecutionId']

    def wait_for_result(self, query_timeout_in_seconds=None):
        if query_timeout_in_seconds is None:
            query_timeout_in_seconds = self._query_timeout

        sleep_in_seconds = 1
        current_wait_time = 0
        while current_wait_time <= query_timeout_in_seconds:

            self._update_query_status()

            if self._query_state in ["SUCCEEDED"]:
                return None
            elif self._query_state in ["CANCELED", "FAILED"]:
                error_string = "Query Execution Failed, Id: {} - StateChangeReason {}".format(
                    self._query_execution_id,
                    self._state_change_reason
                )
                raise RuntimeError(error_string)
            else:
                # Either Queued or Running
                pass

            current_wait_time += sleep_in_seconds
            time.sleep(sleep_in_seconds)

        raise TimeoutError("The Athena query took longer than {} seconds to run! (It's still running)".format(
            query_timeout_in_seconds))

    def get_result(self):
        if self._query_execution_id is None:
            raise RuntimeError("This query hasn't yet been executed, can't retrieve the result!")

        # Wait until the query has been successfully executed
        self.wait_for_result()

        client = self._boto3_session.client('athena')

        # Return the result
        return client.get_query_results(
            QueryExecutionId=self._query_execution_id
        )
