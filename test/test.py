from datetime import datetime, timedelta
from pprint import pprint

import boto3
import pytz

if __name__ == '__main__':

    client = boto3.client('cloudwatch')

    metric_data_queries = [
        {
            'Id': 'cpu_utilization',
            'MetricStat': {
                'Metric': {
                    'Namespace': 'AWS/EC2',
                    'MetricName': 'CPUUtilization',
                    'Dimensions': [
                        {
                            'Name': 'InstanceId',
                            'Value': 'i-0e906d0ae1f9d033b'
                        }
                    ]
                },
                'Period': 10,
                'Stat': 'Average',
                'Unit': 'Percent'
            },
            'Label': 'CPUUtilization',
            'ReturnData': True,
        }
    ]
    end = datetime.now(tz=pytz.timezone('utc'))
    start = end - timedelta(minutes=15)

    response = client.get_metric_data(
        MetricDataQueries=metric_data_queries,
        StartTime=start,
        EndTime=end
    )

    pprint(response)

