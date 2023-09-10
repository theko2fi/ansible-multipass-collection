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
  module = AnsibleModule(argument_spec=dict(
    key = dict(required=True, type='str')
    )
  )
  
  key = module.params.get('key')

  try:
    output = MultipassClient().get(key=key)
    module.exit_json(changed=False, result=output)
  except Exception as e:
    module.fail_json(msg='An unexpected error occurred: {0}'.format(to_native(e)))


if __name__ == '__main__':
  main()



DOCUMENTATION = '''
---
module: multipass_config_get

short_description: Get Multipass configuration setting

version_added: 0.2.0

description:
  - Get the configuration setting corresponding to the given key, or all settings if no key is specified.
  - Essentially returns the output of C(multipass get <key>) command

notes:
  - Support for multiple keys and wildcards coming...

options:
  key:
    description:
      - Path to the setting whose configured value should be obtained.
      - This key takes the form of a dot-separated path in a hierarchical settings tree
    type: str
    required: true

author:
  - "Kenneth KOFFI (@theko2fi)"
'''

EXAMPLES = '''
- name: Get the driver used by Multipass on the host
  theko2fi.multipass.multipass_config_get:
    key: local.driver
  register: output

- name: Print the driver information
  ansible.builtin.debug:
    var: output.result

- name: Get the disk size of a virtual machine
  # 'foo' is the name of the virtual machine
  theko2fi.multipass.multipass_config_get:
    key: local.foo.disk
  register: foo_disk_size

- name: Print the disk size
  ansible.builtin.debug:
    msg: foo virtual machine disk size is: "{{foo_disk_size.result}}"
'''

RETURN = '''
result:
  description:
    - Facts representing the value of a single setting specified by the O(key) option.
    - Matches the C(multipass get) output.
  returned: always
  type: str
'''
