import yaml

from benchmark.engines.hive.engine import Engine

if __name__ == '__main__':
    engine = Engine()
    engine.launch()
    with open('../configs/workloads/tpcds-ansi.yaml', encoding='utf-8') as file:
        workload = yaml.load(file, yaml.FullLoader)
    database = workload['Database']
    for query in workload['Queries']:
        sql = query['SQL']
        name = query['Name']
        engine.execute_query(database=database, sql=sql, name=name)
