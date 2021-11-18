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
import os
import time

import boto3
import yaml

import configs
from benchmark.core.engine import AbstractEngine
from benchmark.core.query import Query, Status


logger = configs.EXECUTE_LOGGER


class Engine(AbstractEngine):

    def __init__(self, config: dict):
        super().__init__(config)
        self.name = 'Athena'

    def launch(self):
        logger.info(f'{self.name} is launching...')
        logger.info(f'{self.name} has launched.')

    def execute_query(self, query: Query) -> Query:
        logger.debug(f'{self.name} engine is executing query: {query}.')
        query.set_status(Status.EXECUTE)
        try:
            athena_query = AthenaQuery(
                database=query.database,
                query=query.sql
            )
            athena_query.execute()
            result_data = athena_query.get_result()
            logger.info(f"Result rows: {len(result_data['ResultSet']['Rows'])}")

            query.set_status(Status.FINISH)
            logger.info(f'{self.name} engine has finished executing query: {query}.')
        except Exception as e:
            query.set_status(Status.FAIL)
            logger.error(f'{self.name} engines failed to execute query {query}, an error has occurred: {e}')
        return query

    def shutdown(self):
        logger.info(f'{self.name} is shutting down...')
        logger.info(f'{self.name} has shut down. ')


class AthenaQuery:

    def __init__(self, database, query,
                 boto3_session=None,
                 query_timeout=60,
                 query_execution_id=None):
        """
        :param query: SQL query.
        :type query: string
        :param database: The name of database.
        :type: database: string
        :param boto3_session: AWS boto3 session.
        :type boto3_session: boto3.session.Session
        :param query_timeout:
        :type query_timeout: float
        :param query_execution_id: # The unique ID of the query that ran as a result of this request.
        :type query_execution_id: string
        """
        with open(os.path.join(os.environ['RAVEN_HOME'], 'configs', 'engines', 'athena', 'athena.yaml'),
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
        return "Query: {query} Database: {database} Bucket: {bucket}".format(
            query=self._query,
            database=self._database,
            bucket=self._output_location
        )

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
