import random
import math
import yaml
import numpy as np


def workload_generator(distribution, dataset, query_set, length, conf):
    queries = []
    # generate timestamps
    timestamps = []
    if distribution == 'average':
        for i in range(conf['num_queries']):
            timestamps.append(i * length / conf['num_queries'])
    elif distribution == 'random':
        for i in range(conf['num_queries']):
            timestamps.append(random.randint(0, length-1))
    elif distribution == 'normal':
        timestamps = np.random.normal(conf['mu'], conf['sigma'], size=conf['num_queries']).tolist()
        for i, timestamp in enumerate(timestamps):
            if timestamp >= length or timestamp < 0:
                timestamps[i] = random.randint(0, length - 1)
    elif distribution == 'bimodal':
        timestamp1 = np.random.normal(conf['mu1'], conf['sigma1'], size=int(conf['num_queries']/2)).tolist()
        timestamp2 = np.random.normal(conf['mu2'], conf['sigma2'], size=conf['num_queries'] - int(conf['num_queries']/2)).tolist()
        timestamps = timestamp1 + timestamp2
        for i, timestamp in enumerate(timestamps):
            if timestamp >= length or timestamp < 0:
                timestamps[i] = random.randint(0, length - 1)
    elif distribution == 'increase':
        for i in range(conf['num_queries']):
            timestamps.append(math.pow(random.random() * math.pow(length, 1/conf['power']), conf['power']))
    elif distribution == 'shrink':
        for i in range(conf['num_queries']):
            time = math.pow(random.random() * math.pow(length, 1/conf['power']), conf['power'])
            if time > conf['shrink_at']:
                time = math.pow(random.random() * math.pow(length, 1/conf['power']), conf['power'])
                if time > conf['shrink_at']:
                    time = math.pow(random.random() * math.pow(length, 1/conf['power']), conf['power'])
            timestamps.append(time)

    for id, timestamp in enumerate(timestamps):
        query = {
            'at_second': timestamp,
            'id': 'query' + str(id),
            'query': random.choice(query_set)
        }
        queries.append(query)
    query_script = {
        'database': dataset,
        'max_worker_num': len(queries) + 100,
        'queries': queries
    }
    f = open('query_script.yaml', 'w')
    yaml.dump(query_script, f)
    return


if __name__ == '__main__':
    qs = ['Q1','Q2','Q3']
    config = {
        'num_queries': 3600
    }
    workload_generator('average', 'raven_tpch_100_db', qs, 3600, config) # num_queries=3600
    # workload_generator('random', 'raven_tpch_100_db', qs, 3600, config) # num_queries=3600
    # workload_generator('normal', 'raven_tpch_100_db', qs, 3600, config) # num_queries=3600, mu=1200, sigma=600
    # workload_generator('bimodal', 'raven_tpch_100_db', qs, 3600, config) # num_queries=3600, mu1=800, sigma1=300, mu2=2400, sigma2=600
    # workload_generator('increase', 'raven_tpch_100_db', qs, 3600, config) # num_queries=3600, power=2
    # workload_generator('shrink', 'raven_tpch_100_db', qs, 3600, config) # num_queries=3600, power=2, shrink_at=3000