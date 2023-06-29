#!/usr/bin/python3
# -*- coding: utf-8 -*-

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
		recreate = dict(required=False, type=bool, default=False)
		)
	)
    
	vm_name = module.params.get('name')
	image = module.params.get('image')
	cpu = module.params.get('cpu')
	state = module.params.get('state')
	memory = module.params.get('memory')
	disk = module.params.get('disk')
	cloud_init = module.params.get('cloud_init')

	if state in ('present'):
		if not is_vm_exists(vm_name):
			vm = multipassclient.launch(vm_name=vm_name, image=image, cpu=cpu, mem=memory, disk=disk, cloud_init=cloud_init)
			module.exit_json(changed=True, resultat=vm.info())
		else:
			vm = multipassclient.get_vm(vm_name=vm_name)
			if module.params.get('recreate'):
				vm.delete()
				multipassclient.purge()
				vm = multipassclient.launch(vm_name=vm_name, image=image, cpu=cpu, mem=memory, disk=disk, cloud_init=cloud_init)
				module.exit_json(changed=True, resultat=vm.info())
			module.exit_json(changed=False, resultat=vm.info())
	if state in ('absent'):
		if is_vm_deleted(vm_name=vm_name):
			module.exit_json(changed=False)
		else:
			vm = multipassclient.get_vm(vm_name=vm_name)
			try:
				vm.delete()
			except NameError:
				module.exit_json(changed=False)
			module.exit_json(changed=True)


if __name__ == "__main__":
	main()


DOCUMENTATION='''
module: multipass_vm
author: Kenneth KOFFI (@theko2fi)
description: Module to manage Multipass VM
 
options:
  name:
	  description:
      - Name for the VM.
      - If it is C('primary') (the configured primary instance name), the user's home directory is mounted inside the newly launched instance, in C('Home').
	  required: yes
	  type: str
  image:
	  description: The image used to create the VM.
	  required: false
	  type: str
	  default: 'ubuntu-lts'
  cpu:
  memory:
	  description: The amount of RAM to allocate to the VM.
	  required: false
	  type: str
	  default: '1G'
  disk:
	  description:
      - Disk space to allocate to the VM in format C(<number>[<unit>]).
      - Positive integers, in bytes, or with V(K) (kibibyte, 1024B), V(M) (mebibyte), V(G) (gibibyte) suffix.
      - Omitting the unit defaults to bytes.
	  required: false
	  type: str
	  default: '5G'
	cloud_init:
    description: Path or URL to a user-data cloud-init configuration.
    required: False
    type: str
    default: None
  state:
	description: the state of the VM
	  - 'C(absent) - An instance matching the specified name will be stopped and deleted.
      - 'C(present) - Asserts the existence of an instance matching the name and any provided configuration parameters. If no
        instance matches the name, a virtual machine will be created. If an instance matches the name but the provided configuration
        does not match, the instance will be updated, if it can be. If it cannot be updated, it will be removed and re-created
        with the requested config.'
	required: false
	type: str
	default: present
	choices:
	  - present
	  - absent
  recreate:
    description:
      - Use with present and started states to force the re-creation of an existing Virtual machine.
    type: bool
    default: false
'''

EXAMPLES='''
- name: "Create a VM"
  theko2fi.multipass.multipass_vm:
	name: "foo"
	cpu: 2
'''


RETURN = '''
resultat:
	description: return the VM info
'''
