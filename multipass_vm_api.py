#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright 2023 Kenneth KOFFI (@theko2fi)
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)


from ansible.module_utils.basic import AnsibleModule

import requests

def main():
    module = AnsibleModule(
        argument_spec=dict(
            name = dict(required=True, type='str')
            )
        )
    
    r = requests.post(f"http://localhost:9990/instances/{module.params.get('name')}/stop")

    module.exit_json(changed=True, result=r.text)


if __name__ == "__main__":
    main()