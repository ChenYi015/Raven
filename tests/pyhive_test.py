import yaml
from pyhive import hive
from pyhive.exc import OperationalError


class HiveEngine:

    def __init__(self):
        super().__init__()
        self._cursor = None

    def launch(self):
        self._cursor = hive.connect('localhost').cursor()

    def execute_query(self, database: str, sql: str, name: str = None):
        self._cursor.execute(f'use {database}')
        try:
            print(f'Now executing {name}...')
            self._cursor.execute(f'{sql}')
            print(self._cursor.fetchall())
            # print(self._cursor.fetch_logs())
        except OperationalError:
            print(f'An error occurred when executing {name}.')

    def shutdown(self):
        self._cursor.close()
        self._cursor = None


if __name__ == '__main__':
    engine = HiveEngine()
    engine.launch()
    with open('tpcds-1g.yaml', encoding='utf-8') as file:
        workload = yaml.load(file, yaml.FullLoader)
    database = workload['Database']
    for query in workload['Queries']:
        sql = query['SQL']
        name = query['Name']
        engine.execute_query(database=database, sql=sql, name=name)
