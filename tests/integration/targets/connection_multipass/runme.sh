#!/usr/bin/env bash

set -eux

vm_name=connection-test

if multipass list | grep -q "${vm_name}"; then
    multipass delete --purge "${vm_name}" && sleep 2s
fi
multipass launch --name "${vm_name}" && sleep 2s

cat > test_connection.inventory.yml << EOF
all:
    hosts:
        ${vm_name}:
            ansible_host: ${vm_name}
            ansible_connection: 'theko2fi.multipass.multipass'
            ansible_python_interpreter: '/usr/bin/python3'
EOF

multipass delete --purge "${vm_name}"


ansible-playbook -i test_connection.inventory.yml test_connection.yml \
    -e target_hosts="${vm_name}" \
    -e action_prefix= \
    -e local_folder=/tmp/ansible-local \
    -e remote_folder=/tmp/ansible-remote