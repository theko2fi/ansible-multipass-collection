#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright 2023 Kenneth KOFFI <@theko2fi>
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.basic import AnsibleModule  
from multipass import MultipassClient
from ansible.errors import AnsibleError

multipassclient = MultipassClient()

def is_vm_exists(vm_name):
	vm_local = multipassclient.get_vm(vm_name=vm_name)
	try:
		vm_local.info()
		return True
	except NameError:
		return False
	except Exception as e:
		raise AnsibleError(str(e))
	
def get_vm_state(vm_name: str):
	if is_vm_exists(vm_name=vm_name):
		vm = multipassclient.get_vm(vm_name=vm_name)
		vm_info = vm.info()
		vm_state = vm_info.get("info").get(vm_name).get("state")
		return vm_state

def is_vm_deleted(vm_name: str):
	vm_state = get_vm_state(vm_name=vm_name)
	return vm_state == 'Deleted'
	
def is_vm_running(vm_name: str):
	vm_state = get_vm_state(vm_name=vm_name)
	return vm_state == 'Running'

def is_vm_stopped(vm_name: str):
	vm_state = get_vm_state(vm_name=vm_name)
	return vm_state == 'Stopped'


def main():
	module = AnsibleModule(
		argument_spec=dict(
		name = dict(required=True, type='str'),
		image = dict(required=False, type=str, default='ubuntu-lts'),
		cpu = dict(required=False, type=int, default=1),
		memory = dict(required=False, type=str, default='1G'),
		disk = dict(required=False, type=str, default='5G'),
		cloud_init = dict(required=False, type=str, default=None),
		state = dict(required=False, type=str, default='present'),
		recreate = dict(required=False, type=bool, default=False),
		purge = dict(required=False, type=bool, default=False)
		)
	)
    
	vm_name = module.params.get('name')
	image = module.params.get('image')
	cpu = module.params.get('cpu')
	state = module.params.get('state')
	memory = module.params.get('memory')
	disk = module.params.get('disk')
	cloud_init = module.params.get('cloud_init')
	purge = module.params.get('purge')

	if state in ('present', 'started'):
		try:
			if not is_vm_exists(vm_name):
				vm = multipassclient.launch(vm_name=vm_name, image=image, cpu=cpu, mem=memory, disk=disk, cloud_init=cloud_init)
				module.exit_json(changed=True, result=vm.info())
			else:
				vm = multipassclient.get_vm(vm_name=vm_name)
				if module.params.get('recreate'):
					vm.delete(purge=True)
					vm = multipassclient.launch(vm_name=vm_name, image=image, cpu=cpu, mem=memory, disk=disk, cloud_init=cloud_init)
					module.exit_json(changed=True, result=vm.info())

				if state == 'started':
					# we do nothing if the VM is already running
					if is_vm_running(vm_name):
						module.exit_json(changed=False, result=vm.info())
					else:
						# we recover the VM if it was deleted
						if is_vm_deleted(vm_name):
							multipassclient.recover(vm_name=vm_name)
						# We start the VM if it isn't running
						vm.start()
						module.exit_json(changed=True, result=vm.info())

				# we do nothing if the VM is already present
				module.exit_json(changed=False, result=vm.info())
		except Exception as e:
			module.fail_json(msg=str(e))

	if state in ('absent', 'stopped'):
		try:
			if not is_vm_exists(vm_name=vm_name):
				module.exit_json(changed=False)
			else:
				vm = multipassclient.get_vm(vm_name=vm_name)

				if state == 'stopped':
					# we do nothing if the VM is already stopped
					if is_vm_stopped(vm_name=vm_name):
						module.exit_json(changed=False)
					elif is_vm_deleted(vm_name=vm_name):
						module.exit_json(changed=False)
					else:
						# stop the VM if it's running
						vm.stop()
						module.exit_json(changed=True)

				try:
					vm.delete(purge=purge)
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
  cpu:
    description: The number of CPUs of the VM.
    required: false
    type: int
  memory:
    description: The amount of RAM to allocate to the VM.
    required: false
    type: str
    default: 1G
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

requirements:
  - Multipass python SDK
    U(https://github.com/theko2fi/ansible-multipass-collection#external-requirements)
'''

EXAMPLES = '''
- name: Create a VM with default parameters
  theko2fi.multipass.multipass_vm:
    name: foo

- name: Create a VM with custom specs
  theko2fi.multipass.multipass_vm:
    name: foo
    cpu: 2
    memory: 2G
    disk: 5G

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
    cpu: 4
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
            },
            "release": "Ubuntu 22.04.2 LTS",
            "state": "Running"
          }
        }
      }'
'''