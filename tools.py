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
from typing import List

import paramiko


def ssh_exec_commands(hostname: str = 'localhost', commands: List[str] = [], port: int = 22, username: str = 'hadoop',
                      key_name: str = ''):
    if commands is None or len(commands) == 0:
        return
    if key_name == '':
        raise ValueError('EC2 key pair must be specified.')
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if os.name == 'posix':
        key_filename = f'{os.environ["HOME"]}/.aws/{key_name}.pem'
    else:
        key_filename = f'{os.environ["HOMEPATH"]}/.aws/{key_name}.pem'
    ssh.connect(hostname=hostname, port=port, username=username,
                key_filename=key_filename)
    for command in commands:
        stdin, stdout, stderr = ssh.exec_command(command)
        print(stdout.read().decode())
        print(stderr.read().decode())
    ssh.close()
