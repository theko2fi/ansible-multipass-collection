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
	
def is_vm_running(vm_name: str):
	vm_state = get_vm_state(vm_name=vm_name)
	return vm_state == 'Running'


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


# DOCUMENTATION = r'''
# ---
# module: multipass_vm
# author: "Kenneth KOFFI (@theko2fi)"
# short_description: Module to manage Multipass VM
# description:
#   - Longer description of the module.
#   - You might include instructions.
# options:
#   name:
#     description: Name of the VM.
#     required: yes
#     type: str
#   image:
#     description: The image used to create the VM.
#     required: false
#     type: str
#     default: ubuntu-lts
#   cpu:
#     description: The number of CPUs of the VM.
#     required: false
#     type: int
#   memory:
#     description: The amount of RAM to allocate to the VM.
#     required: false
#     type: str
#     default: 1G
#   disk:
#     description:
#       - Disk space to allocate to the VM in format C(<number>[<unit>]).
#       - Positive integers, in bytes, or with V(K) (kibibyte, 1024B), V(M)
#         (mebibyte), V(G) (gibibyte) suffix.
#       - Omitting the unit defaults to bytes.
#     required: false
#     type: str
#     default: 5G
#   cloud_init:
#     description: Path or URL to a user-data cloud-init configuration.
#     required: false
#     type: str
#     default: None
#   state:
#     description:
#       - C(absent) - An instance matching the specified name will be stopped and
#         deleted.
#       - C(present) - Asserts the existence of an instance matching the name and
#         any provided configuration parameters. If no instance matches the name,
#         a virtual machine will be created. If an instance matches the name but
#         the provided configuration does not match, the instance will be updated,
#         if it can be. If it cannot be updated, it will be removed and re-created
#         with the requested config.
#     required: false
#     type: str
#     default: present
#     choices:
#       - present
#       - started
#       - absent
#       - stopped
#   recreate:
#     description: Use with C(present) and C(started) states to force the re-creation
#       of an existing virtual machine.
#     type: bool
#     default: false
# '''


DOCUMENTATION = '''
author:
    - Kenneth KOFFI (!UNKNOWN)
name: multipass
short_description: Run tasks in multipass containers
description:
    - Run commands or put/fetch files to an existing multipass container.
    - Uses the multipass CLI to execute commands in the container. If you prefer
      to directly connect to the multipass daemon, use the
      R(community.multipass.multipass_api,ansible_collections.community.multipass.multipass_api_connection)
      connection plugin.
options:
    remote_addr:
        description:
            - The name of the container you want to access.
        default: inventory_hostname
        vars:
            - name: inventory_hostname
            - name: ansible_host
            - name: ansible_multipass_host
    remote_user:
        description:
            - The user to execute as inside the container.
            - If multipass is too old to allow this (< 1.7), the one set by multipass itself will be used.
        vars:
            - name: ansible_user
            - name: ansible_multipass_user
        ini:
            - section: defaults
              key: remote_user
        env:
            - name: ANSIBLE_REMOTE_USER
        cli:
            - name: user
        keyword:
            - name: remote_user
    multipass_extra_args:
        description:
            - Extra arguments to pass to the multipass command line.
        default: ''
        vars:
            - name: ansible_multipass_extra_args
        ini:
            - section: multipass_connection
              key: extra_cli_args
    container_timeout:
        default: 10
        description:
            - Controls how long we can wait to access reading output from the container once execution started.
        env:
            - name: ANSIBLE_TIMEOUT
            - name: ANSIBLE_multipass_TIMEOUT
              version_added: 2.2.0
        ini:
            - key: timeout
              section: defaults
            - key: timeout
              section: multipass_connection
              version_added: 2.2.0
        vars:
          - name: ansible_multipass_timeout
            version_added: 2.2.0
        cli:
          - name: timeout
        type: integer
'''

EXAMPLES='''
- name: "Create a VM with default parameters"
  theko2fi.multipass.multipass_vm:
	name: "foo"

- name: "Create a VM with custom specs"
  theko2fi.multipass.multipass_vm:
	name: "foo"
	cpu: 2
	memory: 2G
	disk: 5G

- name: "Recreate a VM"
  theko2fi.multipass.multipass_vm:
	name: "foo"
	cpu: 4
	memory: 2G
	disk: 10G
	recreate: true
	
- name: "Delete a VM"
  theko2fi.multipass.multipass_vm:
	name: "foo"
	state: absent
'''


RETURN = '''
resultat:
	description: return the VM info
'''
