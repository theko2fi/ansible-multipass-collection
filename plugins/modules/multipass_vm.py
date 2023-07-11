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
	except Exception as e:
		return False
	
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
		if not is_vm_exists(vm_name):
			try:
				vm = multipassclient.launch(vm_name=vm_name, image=image, cpu=cpu, mem=memory, disk=disk, cloud_init=cloud_init)
				module.exit_json(changed=True, result=vm.info())
			except Exception as e:
				module.fail_json(msg=str(e))
		else:
			vm = multipassclient.get_vm(vm_name=vm_name)
			if module.params.get('recreate'):
				vm.delete(purge=True)
				vm = multipassclient.launch(vm_name=vm_name, image=image, cpu=cpu, mem=memory, disk=disk, cloud_init=cloud_init)
				module.exit_json(changed=True, result=vm.info())
			
			# we do nothing if the VM is already running
			if state == 'started' and is_vm_running(vm_name):
				module.exit_json(changed=False, result=vm.info())
			
			# we start the VM if it was stopped
			if state == 'started' and is_vm_stopped(vm_name):
				try:
					vm.start()
					module.exit_json(changed=True, result=vm.info())
				except Exception as e:
					module.fail_json(msg=str(e))
			
			# we recover the VM and start it if it was deleted
			if state == 'started' and is_vm_deleted(vm_name):
				try:
					multipassclient.recover(vm_name=vm_name)
					vm.start()
					module.exit_json(changed=True, result=vm.info())
				except Exception as e:
					module.fail_json(msg=str(e))
			
			# we do nothing if the VM is already present
			module.exit_json(changed=False, result=vm.info())
	if state in ('absent', 'stopped'):
		if is_vm_deleted(vm_name=vm_name):
			module.exit_json(changed=False)
		else:
			vm = multipassclient.get_vm(vm_name=vm_name)
			# we do nothing if the VM is already stopped
			if state == 'stopped' and is_vm_stopped(vm_name=vm_name):
				module.exit_json(changed=False)

			# stop the VM if it's running
			if state == 'stopped' and is_vm_running(vm_name=vm_name):
				try:
					vm.stop()
					module.exit_json(changed=True)
				except Exception as e:
					module.fail_json(msg=str(e))
			try:
				vm.delete(purge=purge)
			except NameError:
				# we do nothing if the VM doesn't exist
				module.exit_json(changed=False)
			except Exception as e:
				module.fail_json(msg=str(e))
			module.exit_json(changed=True)


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
  - You might include instructions.
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
    description: Use with C(present) and C(started) states to force the re-creation
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
