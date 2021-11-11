import logging
import os
import sys

import boto3
import botocore.exceptions

if __name__ == '__main__':
    logging.basicConfig(level='INFO', stream=sys.stdout)

    # 1. 创建 boto3 session 和 client
    session = boto3.session.Session(region_name='ap-southeast-1')
    client = session.client('cloudformation')

    # 2. 读取模板信息
    stack_name = 'cloudformation-emr-test'
    with open(os.path.join(os.getcwd(), '..', 'configs', 'providers', 'aws', 'EMR-CloudFormation-for-Spark-SQL.yaml'),
              encoding='utf-8') as file:
        template_body = file.read()

    # 3. 如果 stack 已经存在, 则将其删除
    try:
        logging.info(f'Deleting stack {stack_name}...')
        client.delete_stack(StackName=stack_name)
        waiter = client.get_waiter('stack_delete_complete')
        waiter.wait(StackName=stack_name)
        logging.info(f'Stack {stack_name} has been deleted.')
    except botocore.exceptions.ClientError as error:
        logging.info(error.response)
    except botocore.exceptions.WaiterError as error:
        logging.info(error.last_response)

    # 4. 创建 stack
    try:
        logging.info(f'Creating stack {stack_name}...')
        response = client.create_stack(
            StackName=stack_name,
            TemplateBody=template_body,
            Capabilities=['CAPABILITY_NAMED_IAM']
        )
        waiter = client.get_waiter('stack_create_complete')
        waiter.wait(StackName=stack_name)
        logging.info(f'Stack {stack_name} has been created.')
    except botocore.exceptions.ClientError as error:
        if error.response['Fail']['Code'] == 'AlreadyExistsException':
            logging.info(f'Stack {stack_name} already exists.')
        logging.info(error.response)
