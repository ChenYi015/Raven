import logging
import os
import time
from typing import Optional, Dict

import boto3
from botocore.exceptions import ClientError, WaiterError

from config.engine.kylin.constants import KylinConfig
from config.engine.kylin.constants import KylinFile
from .utils import stack_to_map, read_template


class AWSInstance:

    def __init__(self, config):
        # DEPLOY_PLATFORM
        self.config = config
        self.region = config['AWS_REGION']
        self.cf_client = boto3.client('cloudformation', region_name=self.region)
        if self.config['DEPLOY_PLATFORM'] == 'ec2':
            self._init_ec2_env()
        else:
            self._init_emr_env()

    def _init_ec2_env(self):
        self.ec2_client = boto3.client('ec2', region_name=self.region)
        self.ssm_client = boto3.client('ssm', region_name=self.region)
        self.yaml_path = os.path.join(os.environ['RAVEN_HOME'], 'configs', 'engines', 'kylin4')
        self.create_complete_waiter = self.cf_client.get_waiter('stack_create_complete')
        self.delete_complete_waiter = self.cf_client.get_waiter('stack_delete_complete')

    def _init_emr_env(self):
        # TODO: add emr method and other feature
        pass

    def create_vpc_stack(self) -> Optional[Dict]:
        if self._stack_complete(self.config[KylinConfig.VPC_STACK]):
            logging.info(f"{self.config[KylinConfig.VPC_STACK]} already created complete.")
            return

        response = self.create_stack(
            stack_name=self.config[KylinConfig.VPC_STACK],
            file_path=os.path.join(self.yaml_path, KylinFile.VPC_YAML),
            params={}
        )
        return response

    def delete_vpc_stack(self) -> Optional[Dict]:
        if not self._stack_delete_complete(self.config[KylinConfig.VPC_STACK]):
            logging.warning(f"{self.config[KylinConfig.VPC_STACK]} already terminated complete.")
            return

        resp = self.delete_stack(self.config[KylinConfig.VPC_STACK])
        return resp

    def create_distribution_stack(self) -> Optional[Dict]:
        if self._stack_complete(self.config[KylinConfig.DISTRIBUTION_STACK]):
            logging.warning(f"{self.config[KylinConfig.DISTRIBUTION_STACK]} already created complete.")
            return
        if not self._stack_complete(self.config[KylinConfig.VPC_STACK]):
            logging.warning(f"{self.config[KylinConfig.VPC_STACK]} Must be created complete "
                            f"before create {self.config[KylinConfig.DISTRIBUTION_STACK]}.")
            raise Exception(f"{self.config[KylinConfig.VPC_STACK]} Must be created complete "
                            f"before create {self.config[KylinConfig.DISTRIBUTION_STACK]}.")
        # Note: the stack name must be pre-step's
        params: dict = self._merge_params(
            stack_name=self.config[KylinConfig.VPC_STACK],
            param_name=KylinConfig.EC2_DISTRIBUTION_PARAMS,
            config=self.config
        )
        resp = self.create_stack(
            stack_name=self.config[KylinConfig.DISTRIBUTION_STACK],
            file_path=os.path.join(self.yaml_path, KylinFile.DISTRIBUTION_YAML),
            params=params,
            capability='CAPABILITY_NAMED_IAM'
        )
        return resp

    def delete_distribution_stack(self) -> Optional[Dict]:
        if self._stack_delete_complete(self.config[KylinConfig.DISTRIBUTION_STACK]):
            logging.warning(f"{self.config[KylinConfig.DISTRIBUTION_STACK]} already terminated complete.")
            return
        self.backup_metadata_before_ec2_terminate(
            stack_name=self.config[KylinConfig.DISTRIBUTION_STACK],
            config=self.config
        )
        resp = self.delete_stack(stack_name=self.config[KylinConfig.DISTRIBUTION_STACK])
        return resp

    def create_master_stack(self) -> Optional[Dict]:
        if self._stack_complete(self.config[KylinConfig.MASTER_STACK]):
            logging.warning(f"{self.config[KylinConfig.MASTER_STACK]} already created complete.")
            return
        if not self._stack_complete(self.config[KylinConfig.DISTRIBUTION_STACK]):
            logging.warning(f"{self.config[KylinConfig.DISTRIBUTION_STACK]} Must be created complete "
                            f"before create {self.config[KylinConfig.MASTER_STACK]}.")
            raise Exception(f"{self.config[KylinConfig.DISTRIBUTION_STACK]} Must be created complete "
                            f"before create {self.config[KylinConfig.MASTER_STACK]}.")
        # Note: the stack name must be pre-step's
        params: dict = self._merge_params(
            stack_name=self.config[KylinConfig.DISTRIBUTION_STACK],
            param_name=KylinConfig.EC2_MASTER_PARAMS,
            config=self.config,
        )
        resp = self.create_stack(
            stack_name=self.config[KylinConfig.MASTER_STACK],
            file_path=os.path.join(self.yaml_path, KylinFile.MASTER_YAML),
            params=params
        )
        return resp

    def delete_master_stack(self) -> Optional[Dict]:
        if self._stack_delete_complete(self.config[KylinConfig.MASTER_STACK]):
            logging.warning(f"{self.config[KylinConfig.MASTER_STACK]} already terminated complete.")
            return

        resp = self.delete_stack(stack_name=self.config[KylinConfig.MASTER_STACK])
        return resp

    def create_slave_stack(self) -> Optional[Dict]:
        if self._stack_complete(self.config[KylinConfig.SLAVE_STACK]):
            logging.warning(f"{self.config[KylinConfig.SLAVE_STACK]} already created complete.")
            return
        if not self._stack_complete(self.config[KylinConfig.MASTER_STACK]):
            logging.warning(f"{self.config[KylinConfig.MASTER_STACK]} Must be created complete "
                            f"before create {self.config[KylinConfig.SLAVE_STACK]}.")
            raise Exception(f"{self.config[KylinConfig.MASTER_STACK]} Must be created complete "
                            f"before create {self.config[KylinConfig.SLAVE_STACK]}.")
        # Note: the stack name must be pre-step's
        params: dict = self._merge_params(
            stack_name=self.config[KylinConfig.MASTER_STACK],
            param_name=KylinConfig.EC2_SLAVE_PARAMS,
            config=self.config,
        )
        resp = self.create_stack(
            stack_name=self.config[KylinConfig.SLAVE_STACK],
            file_path=os.path.join(self.yaml_path, KylinFile.SLAVE_YAML),
            params=params
        )
        return resp

    def delete_slave_stack(self) -> Optional[Dict]:
        if self._stack_delete_complete(self.config[KylinConfig.SLAVE_STACK]):
            logging.warning(f"{self.config[KylinConfig.SLAVE_STACK]} already terminated complete.")
            return

        resp = self.delete_stack(stack_name=self.config[KylinConfig.SLAVE_STACK])
        return resp

    def create_raven_client_stack(self) -> Optional[Dict]:
        if self._stack_complete(self.config[KylinConfig.RAVEN_CLIENT_STACK]):
            logging.warning(f"{self.config[KylinConfig.RAVEN_CLIENT_STACK]} already created complete.")
            return
        if not self._stack_complete(self.config[KylinConfig.MASTER_STACK]):
            logging.warning(f"{self.config[KylinConfig.MASTER_STACK]} Must be created complete "
                            f"before create {self.config[KylinConfig.RAVEN_CLIENT_STACK]}.")
            raise Exception(f"{self.config[KylinConfig.MASTER_STACK]} Must be created complete "
                            f"before create {self.config[KylinConfig.RAVEN_CLIENT_STACK]}.")
        # Note: the stack name must be pre-step's
        params: dict = self._merge_params(
            stack_name=self.config[KylinConfig.MASTER_STACK],
            param_name=KylinConfig.EC2_RAVEN_CLIENT_PARAMS,
            config=self.config
        )
        resp = self.create_stack(
            stack_name=self.config[KylinConfig.RAVEN_CLIENT_STACK],
            file_path=os.path.join(self.yaml_path, KylinFile.RAVEN_CLIENT_YAML),
            params=params,
        )
        return resp

    def terminate_raven_client_stack(self) -> Optional[Dict]:
        if self._stack_delete_complete(self.config[KylinConfig.RAVEN_CLIENT_STACK]):
            logging.warning(f"{self.config[KylinConfig.RAVEN_CLIENT_STACK]} already terminated complete.")
            return
        resp = self.delete_stack(stack_name=self.config[KylinConfig.RAVEN_CLIENT_STACK])
        return resp

    def create_emr_for_kylin4_stack(self) -> Optional[Dict]:
        if self._stack_complete(self.config[KylinConfig.EMR_FOR_KYLIN4_STACK]):
            logging.warning(f"{self.config[KylinConfig.EMR_FOR_KYLIN4_STACK]} already created complete.")
            return

        # Note: the stack name must be pre-step's
        params: dict = self._merge_params(
            stack_name=self.config[KylinConfig.VPC_STACK],
            param_name=KylinConfig.EMR_FOR_KYLIN4_PARAMS,
            config=self.config,
        )
        resp = self.create_stack(
            stack_name=self.config[KylinConfig.EMR_FOR_KYLIN4_STACK],
            file_path=os.path.join(self.yaml_path, KylinFile.SLAVE_YAML),
            params=params
        )
        return resp

    def terminate_emr_for_kylin_stack(self) -> Optional[Dict]:
        if self._stack_delete_complete(self.config[KylinConfig.EMR_FOR_KYLIN4_STACK]):
            logging.warning(f"{self.config[KylinConfig.EMR_FOR_KYLIN4_STACK]} already terminated complete.")
            return
        self.backup_metadata_before_emr_terminate(self.config)

        resp = self.delete_stack(stack_name=self.config[KylinConfig.EMR_FOR_KYLIN4_STACK])
        return resp

    def create_kylin4_step_on_emr_stack(self) -> Optional[Dict]:
        if self._stack_complete(self.config[KylinConfig.EMR_FOR_KYLIN4_STACK]):
            logging.warning(f"{self.config[KylinConfig.EMR_FOR_KYLIN4_STACK]} already created complete.")
            return
        # Note: the stack name must be pre-step's
        params: dict = self._merge_params(
            stack_name=self.config[KylinConfig.VPC_STACK],
            param_name=KylinConfig.KYLIN4_STEP_ON_EMR_PARAMS,
            config=self.config,
        )
        resp = self.create_stack(
            stack_name=self.config[KylinConfig.EMR_FOR_KYLIN4_STACK],
            file_path=os.path.join(self.yaml_path, KylinFile.SLAVE_YAML),
            params=params
        )
        return resp

    def backup_metadata_before_ec2_terminate(self, stack_name: str, config: dict) -> Dict:
        if stack_name != config[KylinConfig.DISTRIBUTION_STACK]:
            logging.warning(f"Only {config[KylinConfig.DISTRIBUTION_STACK]} should backup before terminate.")
            return
        backup_command = 'mysqldump -h$(hostname -i) -uroot -p123456 --databases kylin hive ' \
                         '--add-drop-database >  /home/ec2-user/metadata-backup.sql'
        resource_type = 'Ec2InstanceIdOfDistributionNode'
        # NOTE: name_or_id must be instance id!
        instance_id = self.get_specify_resource_from_output(stack_name, resource_type)
        self.exec_script_instance_and_return(name_or_id=instance_id, script=backup_command)
        cp_to_s3_command = f"aws s3 cp /home/ec2-user/metadata-backup.sql {config['BackupMetadataBucketFullPath']} " \
                           f"--region {config['AWS_REGION']}"
        self.exec_script_instance_and_return(name_or_id=instance_id, script=cp_to_s3_command)

    def backup_metadata_before_emr_terminate(self, stack_name: str, config: dict) -> Dict:
        if stack_name != config[KylinConfig.DISTRIBUTION_STACK]:
            logging.warning(f"Only {config[KylinConfig.EMR_FOR_KYLIN4_STACK]} should backup before terminate.")
            return
        # FIXME: fix this
        command = f"mysqldump -h$(hostname -i) -uadmin -p123456 " \
                  f"--databases kylin hive --add-drop-database >  /home/hadoop/metadata-backup.sql"
        self.exec_script_instance_and_return(name_or_id=stack_name, script=command)

    def create_stack(self, stack_name: str, file_path: str, params: dict, capability: str = None) -> Dict:
        if capability:
            resp = self.cf_client.create_stack(
                StackName=stack_name,
                TemplateBody=read_template(file_path),
                Parameters=[{'ParameterKey': k, 'ParameterValue': v} for k, v in params.items()],
                Capabilities=[capability]
            )
        else:
            resp = self.cf_client.create_stack(
                StackName=stack_name,
                TemplateBody=read_template(file_path),
                Parameters=[{'ParameterKey': k, 'ParameterValue': v} for k, v in params.items()],
            )

        assert self._stack_complete(stack_name=stack_name), \
            f"Stack {stack_name} not create complete, pls check."
        return resp

    def delete_stack(self, stack_name: str) -> Dict:
        resp = self.cf_client.delete_stack(StackName=stack_name)
        return resp

    def get_specify_resource_from_output(self, stack_name: str, resource_type: str) -> str:
        output = self.get_stack_output(stack_name)
        return output[resource_type]

    def get_stack_output(self, stack_name: str) -> Dict:
        is_complete = self._stack_complete(stack_name)
        if not is_complete:
            raise Exception(f"{stack_name} is not complete, please check.")
        output = self.cf_client.describe_stacks(StackName=stack_name)
        """current output format:
        {
            'Stacks' : [{
                            ...,
                            Outputs: [
                                        {
                                            'OutputKey': 'xxx',
                                            'OutputValue': 'xxx',
                                            'Description': ...    
                                        }, 
                                        ...]
                        }],
            'ResponseMEtadata': {...}
        }
        """
        handled_outputs = {entry['OutputKey']: entry['OutputValue']
                           for entry in list(output['Stacks'][0]['Outputs'])}

        return handled_outputs

    def is_ec2_stack_ready(self) -> bool:
        if not (
                self._stack_complete(self.config[KylinConfig.VPC_STACK])
                and self._stack_complete(self.config[KylinConfig.DISTRIBUTION_STACK])
                and self._stack_complete(self.config[KylinConfig.MASTER_STACK])
                and self._stack_complete(self.config[KylinConfig.SLAVE_STACK])
        ):
            return False
        return True

    def is_ec2_stack_terminated(self) -> bool:
        deleted_cost_stacks: bool = (
                self._stack_delete_complete(self.config[KylinConfig.DISTRIBUTION_STACK])
                and self._stack_delete_complete(self.config[KylinConfig.MASTER_STACK])
                and self._stack_delete_complete(self.config[KylinConfig.SLAVE_STACK]))
        if deleted_cost_stacks and \
                ((not self.config['ALWAYS_DESTROY_ALL'])
                 or (self._stack_delete_complete(self.config[KylinConfig.VPC_STACK]))):
            return True
        return False

    def is_emr_stack_ready(self) -> Dict:
        if not (self._stack_complete(self.config[KylinConfig.VPC_STACK])
                and self._stack_complete(self.config[KylinConfig.EMR_FOR_KYLIN4_STACK])
                and self._stack_complete(self.config[KylinConfig.KYLIN4_STEP_ON_EMR_STACK])):
            return False
        return True

    def is_emr_stack_terminated(self) -> bool:
        deleted_cost_stacks: bool = self._stack_delete_complete(self.config[KylinConfig.EMR_FOR_KYLIN4_STACK])
        if deleted_cost_stacks and \
                ((not self.config['ALWAYS_DESTROY_ALL'])
                 or (self._stack_delete_complete(self.config[KylinConfig.VPC_STACK]))):
            return True
        return False

    def send_command(self, **kwargs) -> Dict:
        instance_ids = kwargs['vm_name']
        script = kwargs['script']
        document_name = "AWS-RunShellScript"
        parameters = {'commands': [script]}
        response = self.ssm_client.send_command(
            InstanceIds=instance_ids,
            DocumentName=document_name,
            Parameters=parameters
        )
        return response

    def get_command_invocation(self, command_id, instance_id) -> Dict:
        response = self.ssm_client.get_command_invocation(CommandId=command_id, InstanceId=instance_id)
        return response

    def exec_script_instance_and_return(self, name_or_id: str, script: str, timeout: int = 20) -> Dict:
        vm_name = None
        if isinstance(name_or_id, str):
            vm_name = [name_or_id]
        response = self.send_command(vm_name=vm_name, script=script)
        command_id = response['Command']['CommandId']
        time.sleep(5)
        start = time.time()
        output = None
        while time.time() - start < timeout * 60:
            output = self.get_command_invocation(
                command_id=command_id,
                instance_id=name_or_id,
            )
            if output['Status'] in ['Delayed', 'Success', 'Cancelled', 'TimedOut', 'Failed']:
                break
            time.sleep(10)
        assert output and output['Status'] == 'Success', \
            f"execute_queries script failed, failed info: {output['StandardErrorContent']}"

    def stop_ec2_instance(self, instance_id: str):
        self.ec2_client.stop_instances(
            InstanceIds=[
                instance_id,
            ],
            Force=True
        )

    def stop_ec2_instances(self, instance_ids: list):
        self.ec2_client.stop_instances(
            InstanceIds=instance_ids,
            Force=True
        )

    def start_ec2_instance(self, instance_id: str) -> Dict:
        resp = self.ec2_client.start_instances(
            InstanceIds=[instance_id]
        )
        return resp

    def start_ec2_instances(self, instance_ids: list) -> Dict:
        resp = self.ec2_client.start_instances(
            InstanceIds=instance_ids,
        )
        return resp

    def scale_up_workers(self, worker_num: int) -> Optional[Dict]:
        """
        add workers for kylin to scale spark-3.1.1 worker
        :param worker_num: the worker mark
        :param master_addr: which master node to associated
        :return: worker private ip
        """
        if self._stack_complete(self.config[KylinConfig.SLAVE_SCALE_WORKER.format(worker_num)]):
            logging.warning(f"{self.config[KylinConfig.SLAVE_SCALE_WORKER.format(worker_num)]} "
                            f"already created complete.")
            return

            # Note: the stack name must be pre-step's
        params: dict = self._merge_params(
            stack_name=self.config[KylinConfig.MASTER_STACK],
            param_name=KylinConfig.EC2_SCALE_SLAVE_PARAMS,
            config=self.config,
        )
        params.update({'WorkerNum': worker_num})

        resp = self.create_stack(
            stack_name=self.config[KylinConfig.SLAVE_SCALE_WORKER.format(worker_num)],
            file_path=os.path.join(self.yaml_path, KylinFile.SLAVE_SCALE_YAML),
            params=params
        )
        return resp

    def scale_down_worker(self, worker_num: int) -> Optional[Dict]:
        if not self._stack_delete_complete(self.config[KylinConfig.SLAVE_SCALE_WORKER.format(worker_num)]):
            logging.warning(f"{self.config[KylinConfig.SLAVE_SCALE_WORKER.format(worker_num)]} "
                            f"already terminated complete.")
            return
        stack_name = self.config[KylinConfig.SLAVE_SCALE_WORKER.format(worker_num)]
        resource_type = 'SlaveEc2InstanceId'
        # NOTE: name_or_id must be instance id!
        instance_id = self.get_specify_resource_from_output(stack_name, resource_type)

        backup_command = 'source ~/.bash_profile && ${SPARK_HOME}/sbin/decommission-worker.sh'
        self.exec_script_instance_and_return(name_or_id=instance_id, script=backup_command)
        # FIXME: hard code for sleep spark-3.1.1 worker to execute_queries remaining jobs
        # sleep 5 min to ensure all jobs in decommissioned workers are done
        time.sleep(60 * 5)

        # before terminate and delete stack, the worker should be decommissioned.
        resp = self.delete_stack(stack_name)
        return resp

    def _stack_exists(self, stack_name: str, required_status: str = 'CREATE_COMPLETE') -> bool:
        return self._stack_status_check(name_or_id=stack_name, status=required_status)

    def _stack_deleted(self, stack_name: str, required_status: str = 'DELETE_COMPLETE') -> bool:
        return self._stack_status_check(name_or_id=stack_name, status=required_status)

    def _stack_status_check(self, name_or_id: str, status: str) -> bool:
        try:
            resp: dict = self.cf_client.describe_stacks(StackName=name_or_id)
        except ClientError:
            return False
        return resp['Stacks'][0]['StackStatus'] == status

    def _stack_complete(self, stack_name: str) -> bool:
        try:
            self.create_complete_waiter.wait(
                StackName=stack_name,
                WaiterConfig={
                    'Delay': 30,
                    'MaxAttempts': 120
                }
            )
        except WaiterError as wx:
            logging.error(wx)
            return False
        return True

    def _stack_delete_complete(self, stack_name: str) -> bool:
        try:
            self.delete_complete_waiter.wait(
                StackName=stack_name,
                WaiterConfig={
                    'Delay': 30,
                    'MaxAttempts': 6
                }
            )
        except WaiterError as wx:
            logging.error(wx)
            return False
        return True

    def _merge_params(self, stack_name: str, param_name: str, config: dict) -> dict:
        # this stack name is pre-stack
        output: dict = self.get_stack_output(stack_name)
        params: dict = config[param_name]

        # stack output mapping relationship
        relate_map = stack_to_map[stack_name]
        for k, v in params.items():
            # if params hasn't default value, use the pre-step output value to fill the param
            if v:
                continue
            params[k] = output[relate_map[k]]
        return params


class AWS:
    @staticmethod
    def aws_ec2_cluster(config) -> Optional[Dict]:
        logging.info('Creating AWS EC2 Cluster...')
        cloud_instance = AWSInstance(config)
        if not cloud_instance.is_ec2_stack_ready():
            cloud_instance.create_vpc_stack()
            cloud_instance.create_distribution_stack()
            cloud_instance.create_master_stack()
            cloud_instance.create_slave_stack()
        if config[KylinConfig.RAVEN_CLIENT_NEEDED]:
            cloud_instance.create_raven_client_stack()
        # return the master stack resources
        resources = cloud_instance.get_stack_output(config[KylinConfig.MASTER_STACK])
        logging.info('Finish creating AWS EC2 Cluster...')
        return resources

    @staticmethod
    def terminate_ec2_cluster(config) -> Optional[Dict]:
        cloud_instance = AWSInstance(config)
        if cloud_instance.is_ec2_stack_terminated():
            logging.warning('ec2 stack already deleted.')
            return
        cloud_instance.delete_slave_stack()
        cloud_instance.delete_master_stack()
        cloud_instance.delete_distribution_stack()
        if config['ALWAYS_DESTROY_ALL'] is True:
            cloud_instance.delete_vpc_stack()
        # don't need to terminate vpc stack, because it's free resource on your aws if don't use it.
        # after terminated all node check again.
        assert cloud_instance.is_ec2_stack_terminated() is True

    @staticmethod
    def aws_emr_cluster(config) -> Dict:
        cloud_instance = AWSInstance(config)
        if not cloud_instance.is_emr_stack_ready():
            cloud_instance.create_vpc_stack()
            cloud_instance.create_emr_for_kylin4_stack()
            cloud_instance.create_kylin4_step_on_emr_stack()
        # return the master stack resources
        resources = cloud_instance.get_stack_output(config[KylinConfig.EMR_FOR_KYLIN4_STACK])
        return resources

    @staticmethod
    def terminate_emr_cluster(config) -> Optional[Dict]:
        cloud_instance = AWSInstance(config)
        if cloud_instance.is_emr_stack_terminated():
            logging.warning('emr stack already deleted.')
            return
        cloud_instance.terminate_emr_for_kylin_stack()
        if config['ALWAYS_DESTROY_ALL'] is True:
            cloud_instance.delete_vpc_stack()
        # don't need to terminate vpc stack, because it's free resource on your aws if don't use it.
        # after terminated all node check again.
        assert cloud_instance.is_emr_stack_terminated() is True

    @staticmethod
    def aws_cloud(config: Dict) -> str:
        if config[KylinConfig.DEPLOY_PLATFORM] == 'ec2':
            response = AWS.aws_ec2_cluster(config)
            # only get the master dns
            # FIXME: fix hard code and get method
            if config[KylinConfig.EC2_MASTER_PARAMS]['AssociatedPublicIp'] == 'true':
                return response.get('MasterEc2InstancePublicIp')
            return response.get('MasterEc2InstancePrivateIp')
        elif config[KylinConfig.DEPLOY_PLATFORM] == 'emr':
            response = AWS.aws_emr_cluster(config)
            return response.get('ClusterMasterPublicDns')

        msg = f'Not supported platform: {config[KylinConfig.DEPLOY_PLATFORM]}.'
        logging.error(msg)
        raise Exception(msg)

    @staticmethod
    def destroy_aws_cloud(config):
        if config[KylinConfig.DEPLOY_PLATFORM] not in ['ec2', 'emr']:
            msg = f'Not supported platform: {config[KylinConfig.DEPLOY_PLATFORM]}.'
            logging.error(msg)
            raise Exception(msg)

        if config[KylinConfig.DEPLOY_PLATFORM] == 'ec2':
            AWS.terminate_ec2_cluster(config)
        elif config[KylinConfig.DEPLOY_PLATFORM] == 'emr':
            AWS.terminate_emr_cluster(config)

    @staticmethod
    def scale_worker_to_ec2(worker_num: int, config: dict):
        if config[KylinConfig.DEPLOY_PLATFORM] != 'ec2':
            msg = f'Not supported platform: {config[KylinConfig.DEPLOY_PLATFORM]}.'
            logging.error(msg)
            raise Exception(msg)
        cloud_instance = AWSInstance(config)
        cloud_instance.scale_up_workers(worker_num)

    @staticmethod
    def scale_down_worker(worker_num: int, config: dict):
        if config[KylinConfig.DEPLOY_PLATFORM] != 'ec2':
            msg = f'Not supported platform: {config[KylinConfig.DEPLOY_PLATFORM]}.'
            logging.error(msg)
            raise Exception(msg)
        cloud_instance = AWSInstance(config)
        cloud_instance.scale_down_worker(worker_num)