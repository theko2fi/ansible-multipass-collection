from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright 2023 Kenneth KOFFI (@theko2fi)
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.basic import AnsibleModule
from ansible.errors import AnsibleError
from ansible_collections.theko2fi.multipass.plugins.module_utils.multipass import MultipassClient, get_existing_mounts
from ansible_collections.theko2fi.multipass.plugins.module_utils.errors import  MountExistsError, MountNonExistentError



multipassclient = MultipassClient()


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name = dict(required=True, type='str'),
            source = dict(type='str'),
            target = dict(required=False, type='str'),
            state = dict(required=False, type=str, default='present', choices=['present','absent']),
            type = dict(type='str', required=False, default='classic', choices=['classic','native']),
            gid_map = dict(type='list', elements='str', required=False, default=[]),
            uid_map = dict(type='list', elements='str', required=False, default=[])
        ),
        required_if = [('state', 'present', ['source'])]
    )

    vm_name = module.params.get('name')
    src = module.params.get('source')
    dest = module.params.get('target')
    state = module.params.get('state')
    gid_map = module.params.get('gid_map')
    uid_map = module.params.get('uid_map')
    mount_type = module.params.get('type')
    
    if state in ('present'):
        dest = dest or src
        target = f"{vm_name}:{dest}"
        try:
            multipassclient.mount(src=src, target=target, uid_maps=uid_map, gid_maps=gid_map, mount_type=mount_type )
            module.exit_json(changed=True, result=get_existing_mounts(vm_name).get(dest))
        except MountExistsError:
            module.exit_json(changed=False, result=get_existing_mounts(vm_name).get(dest))
        except Exception as e:
            module.fail_json(msg=str(e))
    else:
        target = f"{vm_name}:{dest}" if dest else vm_name
        try:
            changed = False if not get_existing_mounts(vm_name=vm_name) else True
            multipassclient.umount(mount=target)
            module.exit_json(changed=changed)
        except MountNonExistentError:
            module.exit_json(changed=False)
        except Exception as e:
            module.fail_json(msg=str(e))
         


if __name__ == "__main__":
  main()



DOCUMENTATION = '''
module: multipass_mount
short_description: Module to manage directory mapping between host and Multipass virtual machine
description:
  - Mount a local directory in a Multipass virtual machine.
  - Unmount a directory from a Multipass virtual machine.
version_added: 0.3.0
options:
  name:
    type: str
    description:
     - Name of the virtual machine to operate on.
    required: true
  source:
    type: str
    description:
     - Path of the local directory to mount
     - Use with O(state=present) to mount the local directory inside the VM.
    required: false
  target:
    type: str
    description:
     - target mount point (path inside the VM).
     - If omitted when O(state=present), the mount point will be the same as the source's absolute path.
     - If omitted when O(state=absent), all mounts will be removed from the named VM.
    required: false
  type:
    description:
      - Specify the type of mount to use.
      - V(classic) mounts use technology built into Multipass.
      - V(native) mounts use hypervisor and/or platform specific mounts.
    type: str
    default: classic
    choices:
      - classic
      - native
  gid_map:
    description:
      - A list of group IDs mapping for use in the mount.
      - Use the Multipass CLI syntax C(<host>:<instance>).
      - File and folder ownership will be mapped from <host> to <instance> inside the VM.
    type: list
    elements: str
    default: []
  uid_map:
    description:
      - A list of user IDs mapping for use in the mount.
      - Use the Multipass CLI syntax C(<host>:<instance>).
      - File and folder ownership will be mapped from <host> to <instance> inside the VM.
    type: list
    elements: str
    default: []
  state:
    description:
      - V(absent) Unmount the O(target) mount point from the VM.
      - V(present) Mount the O(source) directory inside the VM. If the VM is not currently running, the directory will be mounted automatically on next boot.
    type: str
    default: present
    choices:
      - absent
      - present
author:
  - Kenneth KOFFI (@theko2fi)
'''

EXAMPLES = '''
- name: Mount '/root/data' directory from the host to '/root/data' inside the VM named 'healthy-cankerworm'
  theko2fi.multipass.multipass_mount:
    name: healthy-cankerworm
    source: /root/data

- name: Mount '/root/data' to '/tmp' inside the VM
  theko2fi.multipass.multipass_mount:
    name: healthy-cankerworm
    source: /root/data
    target: /tmp
    state: present

- name: Unmount '/tmp' directory from the VM
  theko2fi.multipass.multipass_mount:
    name: healthy-cankerworm
    target: /tmp
    state: absent

- name: Mount directory, set file and folder ownership
  theko2fi.multipass.multipass_mount:
    name: healthy-cankerworm
    source: /root/data
    target: /tmp
    state: present
    type: classic
    uid_map:
      - "50:50"
      - "1000:1000"
    gid_map:
      - "50:50"

- name: Unmount all mount points from the 'healthy-cankerworm' VM
  theko2fi.multipass.multipass_mount:
    name: healthy-cankerworm
    state: absent
'''

RETURN = '''
result:
  description:
    - Empty if O(state=absent).
  returned: when O(state=present)
  type: dict
  sample: {
            "gid_mappings": [
              "0:default"
            ],
            "source_path": "/root/tmp",
            "uid_mappings": [
              "0:default"
            ]
          }
'''