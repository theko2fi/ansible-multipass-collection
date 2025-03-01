# (c) 2023 Kenneth KOFFI <@theko2fi>
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import requests

import ansible.constants as C
from ansible.errors import AnsibleError, AnsibleFileNotFound
from ansible.module_utils.six import text_type, binary_type
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.plugins.connection import ConnectionBase
from ansible.utils.display import Display
from ansible.utils.path import unfrackpath

display = Display()

class Connection(ConnectionBase):
    ''' API based connections '''

    transport = 'theko2fi.multipass.multipass_api'
    has_pipelining = True

    def __init__(self, *args, **kwargs):
        super(Connection, self).__init__(*args, **kwargs)
        self.cwd = None
        self.default_user = "ubuntu"
        self.api_url = "http://localhost:9990/api/v0.1.0"
        self.token = None

    def _connect(self):
        ''' connect to the multipass VM; obtain the token '''
        self._play_context.remote_user = self.default_user

        if not self._connected:
            display.vvv(u"ESTABLISH API CONNECTION FOR USER: {0}".format(self._play_context.remote_user), host=self._play_context.remote_addr)
            self.token = self._get_token()
            self._connected = True
        return self

    def _get_token(self):
        ''' obtain the token using username and password '''
        url = f"{self.api_url}/login/token"
        data = {
            "username": self.get_option('auth_user'),
            "password": self.get_option('auth_password'),
            "grant_type": "password"
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            return response.json()["access_token"]
        except requests.exceptions.RequestException as e:
            raise AnsibleError(f"Failed to obtain token: {e}")

    def exec_command(self, cmd, in_data=None, sudoable=True):
        ''' run a command on the multipass VM over the API '''

        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        display.debug("in multipass_api.exec_command()")

        url = f"{self.api_url}/instances/{self.get_option('remote_addr')}/exec"
        querystring = {"cmd": cmd}
        headers = {"Authorization": f"Bearer {self.token}", "User-Agent": "ansible/2.9"}

        try:
            response = requests.post(url, headers=headers, json=querystring)
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.RequestException as e:
            raise AnsibleError(f"Failed to execute command: {e}")

        display.vvv(u"EXEC {0}".format(to_text(cmd)), host=self._play_context.remote_addr)
        return (result.get("return_code", 0), result.get("stdout", ""), result.get("stderr", ""))

    def put_file(self, in_path, out_path):
        ''' transfer a file from local to the multipass VM over the API '''

        super(Connection, self).put_file(in_path, out_path)

        in_path = unfrackpath(in_path, basedir=self.cwd)
        out_path = unfrackpath(out_path, basedir=self.cwd)

        display.vvv(f"PUT {in_path} TO {self.get_option('remote_addr')}:{out_path}", host=self._play_context.remote_addr)
        if not os.path.exists(to_bytes(in_path, errors='surrogate_or_strict')):
            raise AnsibleFileNotFound(f"file or module does not exist: {to_native(in_path)}")

        url = f"{self.api_url}/instances/{self.get_option('remote_addr')}/transfer"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "User-Agent": "ansible/2.9"
        }

        try:
            with open(in_path, 'rb') as filedata:
                response = requests.post(
                    url,
                    headers=headers,
                    files={"source": filedata},
                    data=dict(destination=out_path)
                )
                response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise AnsibleError(f"Failed to transfer file: {e}")

    def fetch_file(self, in_path, out_path):
        ''' fetch a file from the multipass VM to local over the API '''

        super(Connection, self).fetch_file(in_path, out_path)

        display.vvv(u"FETCH {0}:{1} TO {2}".format(self.get_option('remote_addr'), in_path, out_path), host=self._play_context.remote_addr)

        url = f"{self.api_url}/instances/{self.get_option('remote_addr')}/transfer"
        headers = {"Authorization": f"Bearer {self.token}", "User-Agent": "ansible/2.9"}
        params = {"path": in_path}

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            with open(out_path, 'wb') as filedata:
                filedata.write(response.content)
        except requests.exceptions.RequestException as e:
            raise AnsibleError(f"Failed to fetch file: {e}")

    def close(self):
        ''' terminate the connection; nothing to do here '''
        self._connected = False

DOCUMENTATION = '''
author:
    - Kenneth KOFFI (@theko2fi)
name: theko2fi.multipass.multipass_api
short_description: Run tasks in Multipass virtual machines using the API
description:
    - Run commands or put/fetch files to an existing multipass VM using the Multipass API.
notes:
    - The C(theko2fi.multipass.multipass_api) connection plugin does not support using
      the ``remote_user`` and ``ansible_user`` variables to configure the remote
      user. Remote commands will often default to running as ``ubuntu`` user.
options:
    remote_addr:
        description:
            - The name of the VM you want to access.
        default: inventory_hostname
        vars:
            - name: inventory_hostname
            - name: ansible_host
            - name: ansible_multipass_host
    auth_user:
        description:
            - The username for authentication to obtain the token.
        vars:
            - name: ansible_auth_user
    auth_password:
        description:
            - The password for authentication to obtain the token.
        vars:
            - name: ansible_auth_password
'''

EXAMPLES = '''
# sample inventory.yml file where `foo` is the name of the Multipass VM:
all:
  hosts:
    foo:
      ansible_host: foo
      ansible_connection: theko2fi.multipass.multipass_api
      ansible_auth_user: myuser
      ansible_auth_password: mypassword
      ansible_python_interpreter: /usr/bin/python3

# Execution: ansible-playbook -i inventory.yml playbook.yml
# The playbook tasks will get executed on the multipass VM using the API
'''