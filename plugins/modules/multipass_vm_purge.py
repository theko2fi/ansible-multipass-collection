#!/usr/bin/python
#
# Copyright 2023 Kenneth KOFFI <@theko2fi>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.common.text.converters import to_native

from ansible.module_utils.basic import AnsibleModule  
from ansible_collections.theko2fi.multipass.plugins.module_utils.multipass import Multipass
from ansible_collections.theko2fi.multipass.plugins.module_utils.multipass_api import basic_auth_argument_spec
from ansible_collections.theko2fi.multipass.plugins.module_utils.errors import MultipassAPIAuthenticationError


def list_vm_deleted(multipassclient):
  instancesDeleted = list()
  for instance in multipassclient.list().get('list'):
    if instance.get('state') == 'Deleted':
      instancesDeleted.append(instance)
  
  return instancesDeleted

def main():
  module = AnsibleModule(argument_spec=basic_auth_argument_spec())

  try:
    multipassclient = Multipass(
      multipass_host=module.params.get('multipass_host'),
      multipass_user=module.params.get('multipass_username'),
      multipass_pass=module.params.get('multipass_password')
    ).create_client()
    result = dict()
    result['vm_purged'] = list_vm_deleted(multipassclient)
    if result['vm_purged']:
      multipassclient.purge()
      result['changed']=True
    else:
      # we do nothing if there's no deleted VM to purge
      result['changed']=False
    module.exit_json(**result)
  except MultipassAPIAuthenticationError as e:
      module.fail_json(msg=str(e))
  except Exception as e:
    module.fail_json(msg='An unexpected error occurred: {0}'.format(to_native(e)))


if __name__ == '__main__':
  main()



DOCUMENTATION = '''
---
module: multipass_vm_purge

short_description: Purge all deleted Multipass virtual machines permanently

version_added: 0.2.0

description:
  - Purge all deleted Multipass instances permanently, including all their data.
  - This will destroy all the traces of the virtual machine, and cannot be undone.
  - Performs the same function as the C(multipass purge) CLI subcommand.

extends_documentation_fragment:
  - theko2fi.multipass.multipass.api_documentation

author:
  - "Kenneth KOFFI (@theko2fi)"
'''

EXAMPLES = '''
- name: Purge all the deleted virtual machines
  theko2fi.multipass.multipass_vm_purge:


# Purge and show the result
- name: Purge all the deleted virtual machines
  theko2fi.multipass.multipass_vm_purge:
  register: result

- name: Display the list of purged virtual machines
  debug:
    var: result.vm_purged

# If you would like to purge a specific VM, use the theko2fi.multipass.multipass_vm module instead
'''

RETURN = '''
vm_purged:
  description:
    - List of purged virtual machines.
  returned: always
  type: list
  elements: dict
  sample: [
      {
        "ipv4": [],
        "name": "ansible-multipass-vm-cbc2f266",
        "release": "Not Available",
        "state": "Deleted"
      }
    ]
'''