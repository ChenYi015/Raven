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
import json
import logging
import time
import uuid

import requests

from benchmark.core.engine import Engine
from benchmark.core.query import Query, QueryStatus

logger = logging.getLogger()


class KylinHttpClient:

    def __init__(self, host, port):
        self._session: requests.Session = requests.Session()
        self._base_url: str = f'http://{host}:{port}'
        self._headers = {
            'Accept': 'application/json',
            'Accept-Language': 'en-US',
            'Content-Type': 'application/json;charset=utf-8'
        }

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        response = self._session.request(method, self._base_url + url, headers=self._headers, **kwargs)
        try:
            response.raise_for_status()
        except requests.exceptions.RequestException as error:
            logger.error(error)
        return response

    def login(self, username: str, password: str) -> requests.Response:
        url = '/kylin/api/user/authentication'
        self._session.auth = (username, password)
        try:
            response = self._request('POST', url)
            response.raise_for_status()
            logger.debug(f'Kylin http client has successfully login.')
            return response
        except requests.exceptions.RequestException as error:
            logger.error(f'Kylin http client failed to login: {error}.')

    def get_job_status(self, job_uuid: str):
        url = '/kylin/api/jobs/{job_uuid}'
        try:
            response = self._request('GET', url)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as error:
            logger.error(f'Kylin http client failed to get status of job {job_uuid}: {error}.')

    def resume_job(self, job_uuid: str):
        url = '/kylin/api/jobs/{job_uuid}/resume'
        try:
            response = self._request('PUT', url)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as error:
            logger.error(f'Kylin http client failed to resume job {job_uuid}: {error}.')

    # Query API
    def query(self, *, project: str = 'Default', sql: str, offset: int = 0, limit: int = 100,
              accept_partial: bool = False, timeout=360):
        """Submit query request to kylin.

        :param project: Project to perform query
        :param sql: The text of sql statement
        :param offset: Query offset
        :param limit: Query limit
        :param accept_partial: Whether accept a partial result or not.
        :param timeout: Request timeout limit.
        :return:
        """
        url = '/kylin/api/query'
        payload = {
            'project': project,
            'sql': sql,
            'offset': offset,
            'limit': limit,
            'acceptPartial': accept_partial,
        }
        response = self._request('POST', url, json=payload, timeout=timeout)
        return response

    def prepare_query(self, project: str, sql: str, offset: int = 0, limit: int = 100, accept_partial: bool = False,
                      timeout=360):
        """Prepare query.

        :param project: Project to perform query
        :param sql: The text of sql statement
        :param offset: Query offset
        :param limit: Query limit
        :param accept_partial: Whether accept a partial result or not.
        :param timeout: Request timeout limit.
        :return
        """
        url = '/kylin/api/query/prestate'
        payload = {
            'project': project,
            'sql': sql,
            'offset': offset,
            'limit': limit,
            'acceptPartial': accept_partial,
        }
        response = self._request('POST', url, json=payload, timeout=timeout)
        return response

    def remove_saved_query(self, query_id: str):
        """Remove saved query.

        :param query_id: The id of saved query you want to remove.
        :return:
        """
        url = f'/kylin/api/saved_queries/{query_id}'
        response = self._request('DELETE', url)
        return response

    def get_saved_queries(self):
        url = '/kylin/api/saved_queries'
        response = self._request('GET', url)
        return response

    def get_running_queries(self):
        url = '/kylin/api/query/runningQueries'
        response = self._request('GET', url)
        return response

    def stop_query(self, query_id: str):
        """Stop query.

        :param query_id: The queryId of you want to stop. You can obtain it by get_running_queries().
        """
        url = f'/kylin/api/query/{query_id}/stop'
        response = self._request('PUT', url)
        return response

    def list_queryable_tables(self, project: str):
        """List queryable tables the project.

        :param project: The project to load tables.
        """
        url = '/kylin/api/tables_and_columns'
        response = self._request('GET', url)
        return response

    # Model API
    def create_model(self, project_name: str, model_name: str, model_desc_data: str):
        url = '/kylin/api/models'
        payload = {
            'project': project_name,
            'modelName': model_name,
            'modelDescData': model_desc_data
        }
        response = self._request('POST', url, json=payload)
        try:
            response.raise_for_status()
            logger.info(f'Kylin http client has successfully created model(project={project_name}, model={model_name}).')
        except requests.exceptions.RequestException as error:
            logger.error(f'Kylin http client failed to create model(project={project_name}, model={model_name}): {error}.')
        return response

    def update_model(self, project_name:  str, model_name: str, model_desc_data: str):
        url = '/kylin/api/models'
        payload = {
            'project': project_name,
            'modelName': model_name,
            'modelDescData': model_desc_data
        }
        response = self._request('PUT', url, json=payload)
        try:
            response.raise_for_status()
            logger.info(
                f'Kylin http client has successfully updated model(project={project_name}, model={model_name}).')
        except requests.exceptions.RequestException as error:
            logger.error(
                f'Kylin http client failed to update model(project={project_name}, model={model_name}): {error}.')
        return response

    def get_model_desc_date(self, project_name: str, model_name: str, offset: int = 0, limit: int = 1):
        url = '/kylin/api/models'
        payload = {
            'projectName': project_name,
            'modelName': model_name,
            'offset': offset,
            'limit': limit
        }
        response = self._request('GET', url, json=payload)
        try:
            response.raise_for_status()
            logger.info(
                f'Kylin http client has successfully got date of model(project={project_name}, model={model_name}).')
        except requests.exceptions.RequestException as error:
            logger.error(
                f'Kylin http client failed to get data of model(project={project_name}, model={model_name}): {error}.')
        return response

    def delete_model(self, model_name):
        url = f'/kylin/api/models/{model_name}'
        response = self._request('DELETE', url)
        try:
            response.raise_for_status()
            logger.info(
                f'Kylin http client has successfully deleted model[{model_name}].')
        except requests.exceptions.RequestException as error:
            logger.error(
                f'Kylin http client failed to delete model model[{model_name}]: {error}.')
        return response

    def clone_model(self, project_name: str, model_name: str):
        url = f'/kylin/api/models/{model_name}/clone'
        payload = {
            'project': project_name,
            'model_name': model_name
        }
        response = self._request('PUT', url)
        try:
            response.raise_for_status()
            logger.info(
                f'Kylin http client has successfully cloned model[{model_name}].')
        except requests.exceptions.RequestException as error:
            logger.error(
                f'Kylin http client failed to clone model model[{model_name}]: {error}.')
        return response

    # Cube API
    def create_cube(self, project_name: str, cube_name: str, cube_desc_data):
        url = '/kylin/api/cubes'
        payload = {
            'project': project_name,
            'cubeName': cube_name,
            'cubeDescData': cube_desc_data
        }
        response = self._request('POST', url, json=payload)
        try:
            response.raise_for_status()
            logger.info('Kylin http client has successfully created cube(project={project_name},cube={cube_name}).')
        except requests.exceptions.RequestException as error:
            logger.error(f'Kylin http client failed to create cube(project={project_name},cube={cube_name}): {error}.')
        return response

    def update_cube(self):
        pass

    def list_cubes(self):
        pass

    def get_cube(self):
        pass

    def get_cube_descriptor(self):
        pass

    def describe_cube(self, cube_name: str, limit: int = 15, offset: int = 0):
        url = f'/kylin/api/cubes?cubeName={cube_name}&limit={limit}&offset={offset}'
        try:
            response = self._request('GET', url)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as error:
            logger.error(f'Kylin http client failed to describe cube {cube_name}: {error}.')

    def build_cube(self, cube_name: str):
        url = f'/kylin/api/cubes/{cube_name}/rebuild'
        try:
            response = self._request('PUT', url)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as error:
            logger.error(f'Kylin http client failed to build cube {cube_name}: {error}.')

    def optimize_cube(self, cube_name: str):
        url = f'/kylin/api/cubes/{cube_name}/optimize2'
        try:
            response = self._request('PUT', url)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as error:
            logger.error(f'Kylin http client failed to optimize cube {cube_name}: {error}.')

    def enable_cube(self):
        pass

    def disable_cube(self):
        pass

    def purge_cube(self):
        pass

    def clone_cube(self):
        pass

    def delete_cube(self):
        pass

    # SSB
    def create_ssb_model(self, scale_factor: int):
        project_name = model_name = f'ssb_flat_tbl_{scale_factor}'
        database = f'ssb_flat_tbl_{scale_factor}'.upper()
        model_desc_data = {
            "uuid": str(uuid.uuid1()),
            "last_modified": 0,
            "version": "4.0.0.0",
            "owner": "ADMIN",
            "name": model_name,
            "is_draft": False,
            "description": "",
            "fact_table": f"{database}.P_LINEORDER",
            "fact_table_alias": "P_LINEORDER",
            "lookups": [
                {
                    "table": f"{database}.PART",
                    "kind": "LOOKUP",
                    "alias": "PART",
                    "join": {
                        "type": "left",
                        "primary_key": [
                            "PART.P_PARTKEY"
                        ],
                        "foreign_key": [
                            "P_LINEORDER.LO_PARTKEY"
                        ]
                    }
                },
                {
                    "table": f"{database}.CUSTOMER",
                    "kind": "LOOKUP",
                    "alias": "CUSTOMER",
                    "join": {
                        "type": "left",
                        "primary_key": [
                            "CUSTOMER.C_CUSTKEY"
                        ],
                        "foreign_key": [
                            "P_LINEORDER.LO_CUSTKEY"
                        ]
                    }
                },
                {
                    "table": f"{database}.SUPPLIER",
                    "kind": "LOOKUP",
                    "alias": "SUPPLIER",
                    "join": {
                        "type": "left",
                        "primary_key": [
                            "SUPPLIER.S_SUPPKEY"
                        ],
                        "foreign_key": [
                            "P_LINEORDER.LO_SUPPKEY"
                        ]
                    }
                },
                {
                    "table": f"{database}.DATES",
                    "kind": "LOOKUP",
                    "alias": "DATES",
                    "join": {
                        "type": "left",
                        "primary_key": [
                            "DATES.D_DATEKEY"
                        ],
                        "foreign_key": [
                            "P_LINEORDER.LO_ORDERDATE"
                        ]
                    }
                }
            ],
            "dimensions": [
                {
                    "table": "P_LINEORDER",
                    "columns": [
                        "LO_QUANTITY",
                        "LO_DISCOUNT",
                        "LO_PARTKEY",
                        "LO_CUSTKEY",
                        "LO_SUPPKEY",
                        "LO_ORDERDATE"
                    ]
                },
                {
                    "table": "PART",
                    "columns": [
                        "P_PARTKEY",
                        "P_MFGR",
                        "P_CATEGORY",
                        "P_BRAND"
                    ]
                },
                {
                    "table": "CUSTOMER",
                    "columns": [
                        "C_CITY",
                        "C_NATION",
                        "C_CUSTKEY",
                        "C_REGION"
                    ]
                },
                {
                    "table": "SUPPLIER",
                    "columns": [
                        "S_CITY",
                        "S_NATION",
                        "S_REGION",
                        "S_SUPPKEY",
                        "S_NAME"
                    ]
                },
                {
                    "table": "DATES",
                    "columns": [
                        "D_YEAR",
                        "D_YEARMONTHNUM",
                        "D_YEARMONTH",
                        "D_WEEKNUMINYEAR",
                        "D_MONTH",
                        "D_DATEKEY"
                    ]
                }
            ],
            "metrics": [
                "P_LINEORDER.LO_REVENUE",
                "P_LINEORDER.LO_SUPPLYCOST",
                "P_LINEORDER.V_REVENUE"
            ],
            "filter_condition": "",
            "partition_desc": {
                "partition_date_column": "P_LINEORDER.LO_ORDERDATE",
                "partition_time_column": None,
                "partition_date_start": 0,
                "partition_date_format": "yyyyMMdd",
                "partition_time_format": "HH:mm:ss",
                "partition_type": "APPEND",
                "partition_condition_builder": "org.apache.kylin.metadata.model.PartitionDesc$DefaultPartitionConditionBuilder"
            },
            "capacity": "MEDIUM",
        }
        model_desc_data = json.dumps(model_desc_data)
        self.create_model(project_name=project_name, model_name=model_name, model_desc_data=model_desc_data)

    def create_ssb_cube(self, scale_factor: int):
        project_name = model_name = cube_name = f'ssb_flat_tbl_{scale_factor}'
        cube_desc_data = {
            "uuid": str(uuid.uuid1()),
            "last_modified": 0,
            "version": "4.0.0.0",
            "name": cube_name,
            "is_draft": False,
            "model_name": model_name,
            "description": "",
            "null_string": None,
            "dimensions": [
                {
                    "name": "LO_QUANTITY",
                    "table": "P_LINEORDER",
                    "column": "LO_QUANTITY",
                    "derived": None
                },
                {
                    "name": "LO_DISCOUNT",
                    "table": "P_LINEORDER",
                    "column": "LO_DISCOUNT",
                    "derived": None
                },
                {
                    "name": "P_MFGR",
                    "table": "PART",
                    "column": "P_MFGR",
                    "derived": None
                },
                {
                    "name": "P_CATEGORY",
                    "table": "PART",
                    "column": "P_CATEGORY",
                    "derived": None
                },
                {
                    "name": "P_BRAND",
                    "table": "PART",
                    "column": "P_BRAND",
                    "derived": None
                },
                {
                    "name": "C_CITY",
                    "table": "CUSTOMER",
                    "column": "C_CITY",
                    "derived": None
                },
                {
                    "name": "C_NATION",
                    "table": "CUSTOMER",
                    "column": "C_NATION",
                    "derived": None
                },
                {
                    "name": "C_REGION",
                    "table": "CUSTOMER",
                    "column": "C_REGION",
                    "derived": None
                },
                {
                    "name": "S_CITY",
                    "table": "SUPPLIER",
                    "column": "S_CITY",
                    "derived": None
                },
                {
                    "name": "S_NATION",
                    "table": "SUPPLIER",
                    "column": "S_NATION",
                    "derived": None
                },
                {
                    "name": "S_REGION",
                    "table": "SUPPLIER",
                    "column": "S_REGION",
                    "derived": None
                },
                {
                    "name": "D_YEAR",
                    "table": "DATES",
                    "column": "D_YEAR",
                    "derived": None
                },
                {
                    "name": "D_YEARMONTHNUM",
                    "table": "DATES",
                    "column": "D_YEARMONTHNUM",
                    "derived": None
                },
                {
                    "name": "D_YEARMONTH",
                    "table": "DATES",
                    "column": "D_YEARMONTH",
                    "derived": None
                },
                {
                    "name": "D_WEEKNUMINYEAR",
                    "table": "DATES",
                    "column": "D_WEEKNUMINYEAR",
                    "derived": None
                }
            ],
            "measures": [
                {
                    "name": "_COUNT_",
                    "function": {
                        "expression": "COUNT",
                        "parameter": {
                            "type": "constant",
                            "value": "1"
                        },
                        "returntype": "bigint"
                    }
                },
                {
                    "name": "P_LINEORDER.V_REVENUE_SUM",
                    "function": {
                        "expression": "SUM",
                        "parameter": {
                            "type": "column",
                            "value": "P_LINEORDER.V_REVENUE"
                        },
                        "returntype": "bigint"
                    }
                },
                {
                    "name": "P_LINEORDER.LO_SUPPLYCOST_SUM",
                    "function": {
                        "expression": "SUM",
                        "parameter": {
                            "type": "column",
                            "value": "P_LINEORDER.LO_SUPPLYCOST"
                        },
                        "returntype": "bigint"
                    }
                },
                {
                    "name": "P_LINEORDER.LO_REVENUE_SUM",
                    "function": {
                        "expression": "SUM",
                        "parameter": {
                            "type": "column",
                            "value": "P_LINEORDER.LO_REVENUE"
                        },
                        "returntype": "bigint"
                    }
                }
            ],
            "dictionaries": [],
            "rowkey": {
                "rowkey_columns": [
                    {
                        "column": "P_LINEORDER.LO_QUANTITY",
                        "encoding": "dict",
                        "encoding_version": 1,
                        "isShardBy": False
                    },
                    {
                        "column": "P_LINEORDER.LO_DISCOUNT",
                        "encoding": "dict",
                        "encoding_version": 1,
                        "isShardBy": False
                    },
                    {
                        "column": "PART.P_MFGR",
                        "encoding": "dict",
                        "encoding_version": 1,
                        "isShardBy": False
                    },
                    {
                        "column": "PART.P_CATEGORY",
                        "encoding": "dict",
                        "encoding_version": 1,
                        "isShardBy": False
                    },
                    {
                        "column": "PART.P_BRAND",
                        "encoding": "dict",
                        "encoding_version": 1,
                        "isShardBy": False
                    },
                    {
                        "column": "CUSTOMER.C_CITY",
                        "encoding": "dict",
                        "encoding_version": 1,
                        "isShardBy": False
                    },
                    {
                        "column": "CUSTOMER.C_NATION",
                        "encoding": "dict",
                        "encoding_version": 1,
                        "isShardBy": False
                    },
                    {
                        "column": "CUSTOMER.C_REGION",
                        "encoding": "dict",
                        "encoding_version": 1,
                        "isShardBy": False
                    },
                    {
                        "column": "SUPPLIER.S_CITY",
                        "encoding": "dict",
                        "encoding_version": 1,
                        "isShardBy": False
                    },
                    {
                        "column": "SUPPLIER.S_NATION",
                        "encoding": "dict",
                        "encoding_version": 1,
                        "isShardBy": False
                    },
                    {
                        "column": "SUPPLIER.S_REGION",
                        "encoding": "dict",
                        "encoding_version": 1,
                        "isShardBy": False
                    },
                    {
                        "column": "DATES.D_YEAR",
                        "encoding": "dict",
                        "encoding_version": 1,
                        "isShardBy": False
                    },
                    {
                        "column": "DATES.D_YEARMONTHNUM",
                        "encoding": "dict",
                        "encoding_version": 1,
                        "isShardBy": False
                    },
                    {
                        "column": "DATES.D_YEARMONTH",
                        "encoding": "dict",
                        "encoding_version": 1,
                        "isShardBy": False
                    },
                    {
                        "column": "DATES.D_WEEKNUMINYEAR",
                        "encoding": "dict",
                        "encoding_version": 1,
                        "isShardBy": False
                    }
                ]
            },
            "hbase_mapping": {
                "column_family": [
                    {
                        "name": "F1",
                        "columns": [
                            {
                                "qualifier": "M",
                                "measure_refs": [
                                    "_COUNT_",
                                    "P_LINEORDER.V_REVENUE_SUM",
                                    "P_LINEORDER.LO_SUPPLYCOST_SUM",
                                    "P_LINEORDER.LO_REVENUE_SUM"
                                ]
                            }
                        ]
                    }
                ]
            },
            "aggregation_groups": [
                {
                    "includes": [
                        "P_LINEORDER.LO_QUANTITY",
                        "P_LINEORDER.LO_DISCOUNT",
                        "DATES.D_YEAR",
                        "DATES.D_YEARMONTHNUM",
                        "DATES.D_WEEKNUMINYEAR"
                    ],
                    "select_rule": {
                        "hierarchy_dims": [
                            [
                                "DATES.D_YEAR",
                                "DATES.D_YEARMONTHNUM",
                                "DATES.D_WEEKNUMINYEAR"
                            ]
                        ],
                        "mandatory_dims": [],
                        "joint_dims": [
                            [
                                "P_LINEORDER.LO_QUANTITY",
                                "P_LINEORDER.LO_DISCOUNT"
                            ]
                        ]
                    }
                },
                {
                    "includes": [
                        "CUSTOMER.C_CITY",
                        "CUSTOMER.C_NATION",
                        "CUSTOMER.C_REGION",
                        "SUPPLIER.S_CITY",
                        "SUPPLIER.S_NATION",
                        "SUPPLIER.S_REGION",
                        "DATES.D_YEAR",
                        "DATES.D_YEARMONTH",
                        "PART.P_MFGR",
                        "PART.P_CATEGORY",
                        "PART.P_BRAND"
                    ],
                    "select_rule": {
                        "hierarchy_dims": [
                            [
                                "SUPPLIER.S_REGION",
                                "SUPPLIER.S_NATION",
                                "SUPPLIER.S_CITY"
                            ],
                            [
                                "CUSTOMER.C_REGION",
                                "CUSTOMER.C_NATION",
                                "CUSTOMER.C_CITY"
                            ],
                            [
                                "PART.P_MFGR",
                                "PART.P_CATEGORY",
                                "PART.P_BRAND"
                            ],
                            [
                                "DATES.D_YEAR",
                                "DATES.D_YEARMONTH"
                            ]
                        ],
                        "mandatory_dims": [],
                        "joint_dims": []
                    }
                }
            ],
            "signature": None,
            "notify_list": [],
            "status_need_notify": [],
            "partition_date_start": 694224000000,
            "partition_date_end": 3153600000000,
            "auto_merge_time_ranges": [],
            "volatile_range": 0,
            "retention_range": 0,
            "engine_type": 6,
            "storage_type": 4,
            "override_kylin_properties": {},
            "cuboid_black_list": [],
            "parent_forward": 3,
            "mandatory_dimension_set_list": [],
            "snapshot_table_desc_list": []
        }
        cube_desc_data = json.dumps(cube_desc_data)
        self.create_cube(project_name=project_name, cube_name=cube_name, cube_desc_data=cube_desc_data)


class KylinEngine(Engine):

    def __init__(self, *, concurrency: int = 1, host: str = 'localhost', port: int = 7070):
        super().__init__(name='Kylin Engine', description='Kylin 4.0.0 OLAP engine.', concurrency=concurrency)
        self._http_client = KylinHttpClient(host, port)
        self._http_client.login(username='ADMIN', password='KYLIN')

    def execute_query(self, query: Query) -> Query:
        logger.info(f'{self.name} is executing {query}.')
        try:
            # FIXME
            response = self._http_client.query(
                project=query.database,
                sql=query.sql,
                limit=10
            )
            response.raise_for_status()
            query.status = QueryStatus.RUNNING
            query.status = QueryStatus.SUCCEEDED
            logger.info(f'{self.name} has finished executing {query}.')
        except requests.exceptions.HTTPError as error:
            query.status = QueryStatus.FAILED
            logger.error(f'{self.name} failed to execute_queries {query}, an error has occurred: {error}')
        return query
