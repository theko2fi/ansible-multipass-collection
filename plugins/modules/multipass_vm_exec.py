#!/usr/bin/python
#
# Copyright (c) 2023, Kenneth KOFFI (@theko2fi)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.theko2fi.multipass.plugins.module_utils.multipass import Multipass
from ansible_collections.theko2fi.multipass.plugins.module_utils.multipass_api import basic_auth_argument_spec
from ansible_collections.theko2fi.multipass.plugins.module_utils.errors import MultipassAPIAuthenticationError

def main():

  argument_spec = basic_auth_argument_spec()

  argument_spec.update(
    name=dict(type='str', required=True),
    command=dict(type='str', required=True),
    workdir=dict(type='str', required=False)
  )

  module = AnsibleModule(argument_spec=argument_spec)

  name = module.params['name']
  command = module.params['command']
  workdir = module.params['workdir']

  try:
    multipassclient = Multipass(
      multipass_host=module.params.get('multipass_host'),
      multipass_user=module.params.get('multipass_username'),
      multipass_pass=module.params.get('multipass_password')
    ).create_client()
  except MultipassAPIAuthenticationError as e:
    module.fail_json(msg=str(e))


  try:
    VM = multipassclient.get_vm(vm_name=name)
    return_code, stdout, stderr = VM.exec(
       cmd_to_execute=command, working_directory=workdir
    )
    module.exit_json(changed=True, rc=return_code, stdout=stdout, stderr=stderr)
  except Exception as e:
    module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()



DOCUMENTATION = '''
---
module: multipass_vm_exec

short_description: Execute command in a Multipass virtual machine

version_added: 0.2.0

description:
  - Executes a command in a Multipass virtual machine.
extends_documentation_fragment:
  - theko2fi.multipass.multipass.api_documentation
options:
  name:
    type: str
    required: true
    description:
      - The name of the virtual machine to execute the command in.
  command:
    type: str
    description:
      - The command to execute.
    required: true
  workdir:
    type: str
    description:
      - The directory to run the command in.

author:
  - "Kenneth KOFFI (@theko2fi)"
'''

EXAMPLES = '''
- name: Run a simple command
  theko2fi.multipass.multipass_vm_exec:
    name: foo
    command: /bin/bash -c "ls -lah"
  register: result

- name: Print stdout
  ansible.builtin.debug:
    var: result.stdout_lines

- name: Run a simple command in a specific working directory
  theko2fi.multipass.multipass_vm_exec:
    name: foo
    command: "ls -la"
    workdir: /tmp
  register: result

- name: Run a simple command (stderr)
  theko2fi.multipass.multipass_vm_exec:
    name: foo
    command: /bin/bash -c "echo Hello world! && echo Hello world! > /dev/stderr"
  register: result

- name: Print stderr lines
  ansible.builtin.debug:
    var: result.stderr_lines
'''

RETURN = '''
stdout:
    type: str
    returned: success
    description:
      - The standard output of the virtual machine command.
stderr:
    type: str
    returned: success
    description:
      - The standard error output of the virtual machine command.
'''