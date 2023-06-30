<!--
Copyright (c) Ansible Project
GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
SPDX-License-Identifier: GPL-3.0-or-later
-->

# Ansible Collection - theko2fi.multipass

This repo contains the `theko2fi.multipass` Ansible Collection. The collection includes many modules and plugins to work with [Multipass](https://multipass.run/).

Please note that this collection is **not** developed by [Canonical](https://canonical.com/) team. Therefore, it's an UNOFFICIAL collection.

## External requirements

Most modules and plugins require the Multipass python SDK which can be installed as follow:

```bash
pip install git+https://github.com/theko2fi/multipass-python-sdk.git
```

If you already have another version of the SDK, you can force the reinstallation as below:

```bash
pip install --force-reinstall git+https://github.com/theko2fi/multipass-python-sdk.git
```

## Collection Documentation

The full documentation can be found at https://theko2fi.github.io/ansible-multipass-collection/branch/main/.
Please check it out.

## Using this collection

Before using the Docker community collection, you need to install the collection with the `ansible-galaxy` CLI:

```bash
ansible-galaxy collection install theko2fi.multipass
```

You can also include it in a `requirements.yml` file and install it via `ansible-galaxy collection install -r requirements.yml` using the format:

```yaml
collections:
- name: theko2fi.multipass
```

See [Ansible Using collections](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html) for more details.

## Contributing to this collection

Any kind of contribution (pull request, bug report, code review) are welcome on the project [GitHub repository](https://github.com/theko2fi/ansible-multipass-collection).

If you want to develop new content for this collection or improve what is already here, the easiest way to work on the collection is to fork the project and work on it there. I would be happy to merge your pull request if it passes the integration test.

You can find more information in the [developer guide for collections](https://docs.ansible.com/ansible/devel/dev_guide/developing_collections.html#contributing-to-collections).


## Licensing

This collection is primarily licensed and distributed as a whole under the GNU General Public License v3.0 or later.

See [LICENSES/GPL-3.0-or-later.txt](https://github.com/theko2fi/ansible-multipass-collection/blob/main/LICENSE) for the full text.