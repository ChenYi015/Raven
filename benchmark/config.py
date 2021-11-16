# Global variables
import os

import yaml

GITHUB_REPO_URL = 'https://github.com/ChenYi015/Raven.git'

with open(os.path.join(os.environ['RAVEN_HOME'], 'configs', 'raven.yaml'), encoding='utf-8') as file:
    config = yaml.load(file, yaml.FullLoader)

PROVIDER_CONFIG = config['Provider']
ENGINE_CONFIG = config['Engine']
TESTPLAN_CONFIG = config['Testplan']
WORKLOAD_CONFIG = config['Workload']
Metrics = config['Metrics']
Scores = config['Scores']

TAGS = [
    {
        'Key': 'Project',
        'Value': 'Raven'
    },
    {
        'Key': 'Owner',
        'Value': 'ChenYi'
    }
]
