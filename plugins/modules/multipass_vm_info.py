#!/usr/bin/python
#
# Copyright 2023 Kenneth KOFFI <@theko2fi>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.common.text.converters import to_native

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.theko2fi.multipass.plugins.module_utils.multipass import MultipassClient 


def main():
  module = AnsibleModule(argument_spec=dict(name = dict(required=True, type='str')))
  
  vm_name = module.params.get('name')

  try:
    vm = MultipassClient().get_vm(vm_name=vm_name)
    module.exit_json(
      changed=False,
      exists=True,
      result=vm.info(),
    )
  except NameError:
    # We return None if the VM does not exist
    module.exit_json(
      changed=False,
      exists=False,
      result=None,
    )
  except Exception as e:
    module.fail_json(msg='An unexpected error occurred: {0}'.format(to_native(e)))


if __name__ == '__main__':
  main()



DOCUMENTATION = '''
---
module: multipass_vm_info

short_description: Retrieves facts about Multipass virtual machine

description:
  - Retrieves facts about a Multipass virtual machine.
  - Essentially returns the output of C(multipass info <name>), similar to what M(theko2fi.multipass.multipass_vm)
    returns for a non-absent virtual machine.

options:
  name:
    description:
      - The name of the virtual machine to inspect.
    type: str
    required: true

author:
  - "Kenneth KOFFI (@theko2fi)"
'''

EXAMPLES = '''
- name: Get infos on virtual machine
  theko2fi.multipass.multipass_vm_info:
    name: foo
  register: output

- name: Does virtual machine exist?
  ansible.builtin.debug:
    msg: "The VM {{ 'exists' if output.exists else 'does not exist' }}"

- name: Print information about virtual machine
  ansible.builtin.debug:
    var: output.result
  when: output.exists
'''

RETURN = '''
exists:
    description:
      - Returns whether the virtual machine exists.
    type: bool
    returned: always
    sample: true
result:
    description:
      - Facts representing the current state of the virtual machine. Matches the multipass info output.
      - Will be V(none) if virtual machine does not exist.
    returned: always
    type: dict
    sample: '{
    "errors": [],
    "info": {
        "foo": {
            "cpu_count": "1",
            "disks": {
                "sda1": {
                    "total": "5120710656",
                    "used": "2200540672"
                }
            },
            "image_hash": "fe102bfb3d3d917d31068dd9a4bd8fcaeb1f529edda86783f8524fdc1477ee29",
            "image_release": "22.04 LTS",
            "ipv4": [
                "172.23.240.92"
            ],
            "load": [
                0.01,
                0.01,
                0
            ],
            "memory": {
                "total": 935444480,
                "used": 199258112
            },
            "mounts": {
            },
            "release": "Ubuntu 22.04.2 LTS",
            "state": "Running"
          }
        }
      }'
'''
