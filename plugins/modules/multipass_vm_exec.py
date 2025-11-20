#!/usr/bin/python
#
# Copyright (c) 2023, Kenneth KOFFI (@theko2fi)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import shlex
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_text, to_bytes
import subprocess
from ansible_collections.theko2fi.multipass.plugins.module_utils.multipass import MultipassVM

def main():
  module = AnsibleModule(
      argument_spec = dict(
        name=dict(type='str', required=True),
        command=dict(type='str', required=True),
        workdir=dict(type='str', required=False)
    )
  )

  name = module.params['name']
  command = module.params['command']
  workdir = module.params['workdir']

  try:
    VM = MultipassVM(vm_name=name, multipass_cmd="multipass")
    stdout, stderr = VM.exec(
       cmd_to_execute=command, working_directory=workdir
      )

    module.exit_json(changed=True, stdout=to_text(stdout, encoding='utf-8'), stderr=to_text(stderr, encoding='utf-8'))
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