#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright 2023 Kenneth KOFFI (@theko2fi)
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.theko2fi.multipass.plugins.module_utils.multipass import MultipassClient, get_existing_mounts
import os, sys


multipassclient = MultipassClient()


class AnsibleMultipassVM:
    def __init__(self, name):
        self.name = name
        self.vm = multipassclient.get_vm(vm_name=name)

    @property
    def is_vm_exists(self):
        try:
            self.vm.info()
            return True
        except NameError:
            return False
        
    def get_vm_state(self):
        vm_state = self.vm.info().get("info").get(self.name).get("state")
        return vm_state
    
    @property
    def is_vm_deleted(self) -> bool:
        return self.get_vm_state() == 'Deleted'
    
    @property
    def is_vm_running(self) -> bool:
        return self.get_vm_state() == 'Running'
    
    @property
    def is_vm_stopped(self) -> bool:
        vm_state = self.get_vm_state()
        return vm_state == 'Stopped'

def compare_dictionaries(dict1, dict2):
    # Check for keys present in dict1 but not in dict2
    keys_only_in_dict1 = set(dict1.keys()) - set(dict2.keys())
    
    # Check for keys present in dict2 but not in dict1
    keys_only_in_dict2 = set(dict2.keys()) - set(dict1.keys())
    
    # Check for common keys and compare values
    keys_with_different_values = {key for key in set(dict1.keys()) & set(dict2.keys()) if dict1[key] != dict2[key]}
    
    if not keys_only_in_dict1 and not keys_only_in_dict2 and not keys_with_different_values:
        is_different = False
    else:
        is_different = True

    return is_different, keys_only_in_dict1, keys_only_in_dict2, keys_with_different_values

def build_expected_mounts_dictionnary(mounts: list):

    expected_mounts = dict()
    
    for mount in mounts:
        source = mount.get('source')
        target = mount.get('target') or source
        # By default, Multipass use the current process gid and uid for mappings
        # On Windows, there is no direct equivalent to the Unix-like concept of user ID (UID)
        # So Multipass seems to use "-2" as default values on Windows (need to be verified)
        gid_mappings = mount.get('gid_map') or [f"{os.getgid()}:default"] if sys.platform not in ("win32","win64") else ["-2:default"]
        uid_mappings = mount.get('uid_map') or [f"{os.getuid()}:default"] if sys.platform not in ("win32","win64") else ["-2:default"]
        expected_mounts[target] = {
            "gid_mappings": gid_mappings,
            "source_path": source,
            "uid_mappings": uid_mappings
            }
    return expected_mounts


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name = dict(required=True, type='str'),
            image = dict(required=False, type=str, default='ubuntu-lts'),
            cpus = dict(required=False, type=int, default=1),
            memory = dict(required=False, type=str, default='1G'),
            disk = dict(required=False, type=str, default='5G'),
            cloud_init = dict(required=False, type=str, default=None),
            state = dict(required=False, type=str, default='present'),
            recreate = dict(required=False, type=bool, default=False),
            purge = dict(required=False, type=bool, default=False),
            networks = dict(type='list', elements='dict', suboptions=dict(
                name=dict(type='str', required=True),
                mode=dict(type='str', choices=['auto', 'manual'], default='auto'),
                mac=dict(type='str'),
                )
            ),
            mounts = dict(type='list', elements='dict', suboptions=dict(
                target=dict(type='str'),
                source=dict(type='str', required=True),
                type=dict(type='str', choices=['classic', 'native'], default='classic'),
                gid_map=dict(type='list', elements='str'),
                uid_map=dict(type='list', elements='str')
                )
            )
        )
    )

    vm_name = module.params.get('name')
    image = module.params.get('image')
    cpus = module.params.get('cpus')
    networks = module.params.get('networks')
    state = module.params.get('state')
    memory = module.params.get('memory')
    disk = module.params.get('disk')
    cloud_init = module.params.get('cloud_init')
    purge = module.params.get('purge')
    mounts = module.params.get('mounts')

    ansible_multipass = AnsibleMultipassVM(vm_name)

    if state in ('present', 'started'):
        try:
            # we create a new VM
            if not ansible_multipass.is_vm_exists:
                vm = multipassclient.launch(
                    vm_name=vm_name,
                    image=image,
                    cpu=cpus,
                    mem=memory,
                    networks=networks,
                    disk=disk,
                    cloud_init=cloud_init
                    )
                changed = True
                #module.exit_json(changed=True, result=vm.info())
            else:
                vm = ansible_multipass.vm
                changed = False

                if state == 'started':
                    # # we do nothing if the VM is already running
                    # if is_vm_running(vm_name):
                    # 	changed=False
                    # 	#module.exit_json(changed=False, result=vm.info())
                    if not ansible_multipass.is_vm_running:
                        # we recover the VM if it was deleted
                        if ansible_multipass.is_vm_deleted:
                            multipassclient.recover(vm_name=vm_name)
                        # We start the VM if it isn't running
                        vm.start()
                        changed = True
                        #module.exit_json(changed=True, result=vm.info())
                
                if module.params.get('recreate'):
                    vm.delete(purge=True)
                    vm = multipassclient.launch(
                        vm_name=vm_name,
                        image=image,
                        cpu=cpus,
                        mem=memory,
                        networks=networks,
                        disk=disk,
                        cloud_init=cloud_init
                        )
                    changed = True
                    #module.exit_json(changed=True, result=vm.info())
                        
            if mounts:
                existing_mounts = get_existing_mounts(vm_name=vm_name)
                expected_mounts = build_expected_mounts_dictionnary(mounts)
                # Compare existing and expected mounts
                is_different, target_paths_only_in_expected_mounts, target_paths_only_in_existing_mounts, different_mounts = compare_dictionaries(expected_mounts, existing_mounts)
                if is_different:
                    changed = True
                    for target_path in target_paths_only_in_existing_mounts:
                        MultipassClient().umount(mount=f"{vm_name}:{target_path}")

                    for target_path in target_paths_only_in_expected_mounts:
                        source_path = expected_mounts.get(target_path).get("source_path")
                        uid_mappings = expected_mounts.get(target_path).get("uid_mappings")
                        gid_mappings = expected_mounts.get(target_path).get("gid_mappings")

                        uid_mappings_cleaned = [uid_mapping for uid_mapping in uid_mappings if not "default" in uid_mapping]
                        gid_mappings_cleaned = [gid_mapping for gid_mapping in gid_mappings if not "default" in gid_mapping]

                        MultipassClient().mount(
                            src=source_path,
                            target=f"{vm_name}:{target_path}",
                            uid_maps=uid_mappings_cleaned,
                            gid_maps=gid_mappings_cleaned
                            )

                    for target_path in different_mounts:
                        MultipassClient().umount(mount=f"{vm_name}:{target_path}")

                        source_path = expected_mounts.get(target_path).get("source_path")
                        uid_mappings = expected_mounts.get(target_path).get("uid_mappings")
                        gid_mappings = expected_mounts.get(target_path).get("gid_mappings")

                        uid_mappings_cleaned = [uid_mapping for uid_mapping in uid_mappings if not "default" in uid_mapping]
                        gid_mappings_cleaned = [gid_mapping for gid_mapping in gid_mappings if not "default" in gid_mapping]

                        MultipassClient().mount(
                            src=source_path,
                            target=f"{vm_name}:{target_path}",
                            uid_maps=uid_mappings_cleaned,
                            gid_maps=gid_mappings_cleaned
                            )


            module.exit_json(changed=changed, result=vm.info())
        except Exception as e:
            module.fail_json(msg=str(e))

    if state in ('absent', 'stopped'):
        try:
            if not ansible_multipass.is_vm_exists:
                module.exit_json(changed=False)
            else:
                if state == 'stopped':
                    # we do nothing if the VM is already stopped
                    if ansible_multipass.is_vm_stopped:
                        module.exit_json(changed=False)
                    elif ansible_multipass.is_vm_deleted:
                        module.exit_json(changed=False)
                    else:
                        # stop the VM if it's running
                        ansible_multipass.vm.stop()
                        module.exit_json(changed=True)							

                try:
                    ansible_multipass.vm.delete(purge=purge)
                    module.exit_json(changed=True)
                except NameError:
                    # we do nothing if the VM doesn't exist
                    module.exit_json(changed=False)
        except Exception as e:
            module.fail_json(msg=str(e))
            


if __name__ == "__main__":
    main()


DOCUMENTATION = '''
---
module: multipass_vm
author: Kenneth KOFFI (@theko2fi)
short_description: Module to manage Multipass VM
description:
  - Manage the life cycle of Multipass virtual machines (create, start, stop,
      delete).
options:
  name:
    description:
      - Name for the VM.
      - If it is C('primary') (the configured primary instance name), the user's
          home directory is mounted inside the newly launched instance, in
          C('Home').
    required: yes
    type: str
  image:
    description: The image used to create the VM.
    required: false
    type: str
    default: ubuntu-lts
  cpus:
    description: The number of CPUs of the VM.
    required: false
    type: int
  networks:
    description: A list of networks to be used in the VM specification.
    required: false
    elements: dict
    type: list
    suboptions:
      name:
        type: str
        description:
          - Name of the host network to connect the instance's device to 
        required: true
      mode:
        type: str
        description:
          - Network mode
          - If it's C('auto') the VM will attempt to configure the network automatically.
        required: false
        default: auto
        choices:
          - auto
          - manual
      mac:
        type: str
        description:
          - Custom MAC address to use for the device.
        required: false
  memory:
    description: The amount of RAM to allocate to the VM.
    required: false
    type: str
    default: 1G
  mounts:
    type: list
    elements: dict
    required: false
    description:
      - Specification for mounts to be added to the VM.
      - Omitting a mount that is currently applied to a VM will remove it.
    version_added: 0.3.0
    suboptions:
      source:
        type: str
        description:
          - Path of the local directory to mount.
        required: true
      target:
        type: str
        description:
          - target mount point (path inside the VM).
          - If omitted, the mount point will be the same as the source's absolute path.
        required: false
      type:
        type: str
        description:
          - Specify the type of mount to use.
          - V(classic) mounts use technology built into Multipass.
          - V(native) mounts use hypervisor and/or platform specific mounts.
        default: classic
        choices:
          - classic
          - native
      uid_map:
        description:
          - A list of user IDs mapping for use in the mount.
          - Use the Multipass CLI syntax C(<host>:<instance>).
            File and folder ownership will be mapped from <host> to <instance> inside the VM.
          - Omitting an uid_map that is currently applied to a mount, will remove it.
        type: list
        elements: str
      gid_map:
        description:
          - A list of group IDs mapping for use in the mount.
          - Use the Multipass CLI syntax C(<host>:<instance>).
            File and folder ownership will be mapped from <host> to <instance> inside the VM.
          - Omitting an gid_map that is currently applied to a mount, will remove it.
        type: list
        elements: str
  disk:
    description:
      - Disk space to allocate to the VM in format C(<number>[<unit>]).
      - Positive integers, in bytes, or with V(K) (kibibyte, 1024B), V(M)
          (mebibyte), V(G) (gibibyte) suffix.
      - Omitting the unit defaults to bytes.
    required: false
    type: str
    default: 5G
  cloud_init:
    description: Path or URL to a user-data cloud-init configuration.
    required: false
    type: str
    default: None
  state:
    description:
      - C(absent) - An instance matching the specified name will be stopped and
          deleted.
      - C(present) - Asserts the existence of an instance matching the name and
          any provided configuration parameters. If no instance matches the name,
          a virtual machine will be created.
      - 'V(started) - Asserts that the VM is first V(present), and then if the VM
          is not running moves it to a running state. If the VM was deleted, it will
          be recovered and started.'
      - 'V(stopped) - If an instance matching the specified name is running, moves
          it to a stopped state.'
      - Use the O(recreate) option to always force re-creation of a matching virtual
          machine, even if it is running.
    required: false
    type: str
    default: present
    choices:
      - present
      - started
      - absent
      - stopped
  purge:
    description: Use with O(state=absent) to purge the VM after successful deletion.
    type: bool
    default: false
  recreate:
    description: Use with O(state=present) or O(state=started) to force the re-creation
        of an existing virtual machine.
    type: bool
    default: false
'''

EXAMPLES = '''
- name: Create a VM with default parameters
  theko2fi.multipass.multipass_vm:
    name: foo

- name: Create a VM with custom specs
  theko2fi.multipass.multipass_vm:
    name: foo
    cpus: 2
    memory: 2G
    disk: 5G
    networks:
      - name: en0

- name: Create a VM with multiple networks
  theko2fi.multipass.multipass_vm:
    name: foo
    cpus: 2
    memory: 2G
    disk: 5G
    networks:
      - name: en0
      - name: bridge0
        mode: manual
        mac: '50:b3:41:6c:83:cd'


- name: Stop a VM
  theko2fi.multipass.multipass_vm:
    name: foo
    state: stopped

- name: Start a VM
  theko2fi.multipass.multipass_vm:
    name: foo
    state: started

- name: Recreate a VM
  theko2fi.multipass.multipass_vm:
    name: foo
    cpus: 4
    memory: 2G
    disk: 10G
    recreate: true

- name: Delete a VM
  theko2fi.multipass.multipass_vm:
    name: foo
    state: absent
        
- name: Delete and purge a VM
  theko2fi.multipass.multipass_vm:
    name: foo
    state: absent
    purge: true
'''

RETURN = '''
---
result:
    description: return the VM info
'''

RETURN = ''' 
result:
  description:
      - Facts representing the current state of the virtual machine. Matches the multipass info output.
      - Empty if O(state=absent) or O(state=stopped).
      - Will be V(none) if virtual machine does not exist.
  returned: success; or when O(state=started) or O(state=present), and when waiting for the VM result did not fail
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
                      "/home/ubuntu/data": {
                          "gid_mappings": [
                              "0:default"
                          ],
                          "source_path": "/tmp",
                          "uid_mappings": [
                              "0:default"
                          ]
                      }
                  },
                  "release": "Ubuntu 22.04.2 LTS",
                  "state": "Running"
              }
          }
      }'
'''