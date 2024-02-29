<!--
Copyright (c) Ansible Project
GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
SPDX-License-Identifier: GPL-3.0-or-later
-->

# Ansible Collection - theko2fi.multipass

This repo contains the `theko2fi.multipass` Ansible Collection. The collection includes many modules and plugins to work with [Multipass](https://multipass.run/).

Please note that this collection is **not** developed by [Canonical](https://canonical.com/) team. Therefore, it's an UNOFFICIAL collection.

## Included content

* Connection plugins:
    - [multipass](https://theko2fi.github.io/ansible-multipass-collection/branch/main/multipass_connection.html) - Run tasks in Multipass virtual machines
* Modules:
    - [multipass_vm](https://theko2fi.github.io/ansible-multipass-collection/branch/main/multipass_vm_module.html) - Module to manage Multipass virtual machines
    - [multipass_vm_info](https://theko2fi.github.io/ansible-multipass-collection/branch/main/multipass_vm_info_module.html) - Module to retrieves facts about Multipass virtual machines
    - [multipass_vm_exec](https://theko2fi.github.io/ansible-multipass-collection/branch/main/multipass_vm_exec_module.html) - Module to execute command in a Multipass virtual machine
    - [multipass_vm_purge](https://theko2fi.github.io/ansible-multipass-collection/branch/main/multipass_vm_purge_module.html) - Module to purge all deleted Multipass virtual machines permanently
    - [multipass_vm_transfer_into](https://theko2fi.github.io/ansible-multipass-collection/branch/main/multipass_vm_transfer_into_module.html) - Module to copy a file into a Multipass virtual machine
    - [multipass_config_get](https://theko2fi.github.io/ansible-multipass-collection/branch/main/multipass_config_get_module.html) - Module to get Multipass configuration setting
    - [multipass_mount](https://theko2fi.github.io/ansible-multipass-collection/branch/main/multipass_mount_module.html) - Module to manage directory mapping between host and Multipass virtual machines
* Roles:
    - molecule_multipass - Molecule Multipass driver 

## Installation

Before using the Multipass collection, you need to install the collection with the `ansible-galaxy` CLI:

```bash
ansible-galaxy collection install theko2fi.multipass
```

You can also include it in a `requirements.yml` file and install it via `ansible-galaxy collection install -r requirements.yml` using the format:

```yaml
collections:
- name: theko2fi.multipass
```

See [Ansible Using collections](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html) for more details.

## Usage

It's preferable to use content in this collection using their Fully Qualified Collection Namespace (FQCN), for example `theko2fi.multipass.multipass_vm`. The sample playbook below will create a Multipass VM, add the VM to the inventory and test the connection to it.

```yaml
---
- name: Prepare
  hosts: localhost
  connection: local
  tasks:
    - name: Create a Multipass VM
      theko2fi.multipass.multipass_vm:
        name: foo
        cpus: 2
        memory: 2G
        disk: 8G
        state: started
    - name: Add the VM to the inventory
      ansible.builtin.add_host:
        name: foo
        ansible_host: foo
        ansible_connection: theko2fi.multipass.multipass
        ansible_python_interpreter: '/usr/bin/python3'

- name: Run a play against the multipass VM
  hosts: foo
  tasks:
    - name: Ping
      ansible.builtin.ping:
```

## Collection Documentation

The full documentation can be found at https://theko2fi.github.io/ansible-multipass-collection/branch/main/.

Please check it out.

## Contributing to this collection

Any kind of contribution (pull request, bug report, code review) are welcome on the project [GitHub repository](https://github.com/theko2fi/ansible-multipass-collection).

If you want to develop new content for this collection or improve what is already here, the easiest way to work on the collection is to fork the project and work on it there. I would be happy to merge your pull request if it passes the integration test.

You can find more information in the [developer guide for collections](https://docs.ansible.com/ansible/devel/dev_guide/developing_collections.html#contributing-to-collections).


## Licensing

This collection is primarily licensed and distributed as a whole under the GNU General Public License v3.0 or later.

See [LICENSES/GPL-3.0-or-later.txt](https://github.com/theko2fi/ansible-multipass-collection/blob/main/LICENSE) for the full text.