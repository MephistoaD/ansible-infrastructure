#!/usr/bin/python3

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: nb_ipam_info

short_description: Returns all IPAM Data from NetBox

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: An Info module returning IP-Addresses, IP-Ranges and the ips for each host.

        api_endpoint=dict(type='str', required=True),
        token=dict(type='str', required=True),
        validate_certs=dict(type='bool', required=False, default=True)

options:
    api_endpoint:
        description: The URL to the NetBox API.
        required: true
        type: str
    token:
        description: The API token for the NetBox instance (read only permissions should be sufficient)
        required: true
        type: str
    validate_certs:
        description: 
            Wether to validate the SSL certificate of the NetBox server.
            options:
            - True (defualt)
            - False
        required: false
        type: bool
# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
# extends_documentation_fragment:
#     - my_namespace.my_collection.my_doc_fragment_name

author:
    - MephistoaD (@MephistoaD)
'''

EXAMPLES = r'''
- name: Get all IPAM info
  nb_ipam_info:
    api_endpoint: "https://netbox.local"
    token: "xxxyyy"
    validate_certs: False
  register: ipam_info
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.

addresses:
    description: A list containing all known IP-Addresses.
    type: dict
    returned: always
    sample: {
            "10.0.0.2/24": {
                "address": "10.0.0.2/24",
                "custom_fields": {},
                "description": "",
                "dns_name": "webserver.local",
                "instance": "webserver",
                "interface": "eth0",
                "tags": []
            },
        }
instances:
    description: A list of the interfaces and their IP-addresses per interface.
    type: dict
    returned: always
    sample: {
        "webserver": {
                "eth0": [
                    "10.0.0.2/24"
                ],
                "wg0": [
                    "10.1.1.1/24"
                ]
            }
        }
ranges:
    description: A list of all known IP-ranges and their IP addresses.
    type: list
    returned: always
    sample: [
            {
                "addresses": [
                    "10.0.0.2/24"
                ],
                "comments": "",
                "custom_fields": {},
                "description": "local network",
                "display": "10.0.0.1-254/24",
                "end_address": "10.0.0.254/24",
                "family": {
                    "label": "IPv4",
                    "value": 4
                },
                "role": null,
                "size": 254,
                "start_address": "10.0.0.1/24",
                "tags": [],
                "vrf": null
            }
            ]
'''

from ansible.module_utils.basic import AnsibleModule

import os
import yaml

def get_all_dependencies(all_roles, roles_dir):
    all_dependencies = {}
    for role in all_roles:
        all_dependencies[role] = get_dependencies(role, roles_dir)
    return all_dependencies

def get_dependencies(role_name, roles_dir):
    dependencies = []

    meta_file = os.path.join(roles_dir, role_name, 'meta', 'main.yml')

    try:
        if os.path.exists(meta_file):
            with open(meta_file, 'r') as f:
                meta_data = yaml.safe_load(f)
                dependencies_raw = meta_data.get('dependencies', [])

                # Check if the specified role_name is in the dependencies
                for d in dependencies_raw:
                    if isinstance(d, dict) and 'role' in d:
                        dependencies.append(d['role'])
                    elif isinstance(d, str):
                        dependencies.append(d)
    except:
        pass

    return dependencies

def list_dependent_roles(role_name, all_roles, first_level_dependencies):
    dependent_roles = set()

    stack = [role_name]
    while stack:
        current_role = stack.pop()
        dependent_roles.add(current_role)
        for role in all_roles:
            for dependency in first_level_dependencies.get(role, []):
                if dependency == current_role:
                    stack.append(role)

    return list(dependent_roles)

def get_prometheus_exporter_port(role_name, roles_dir, inventory_dir):
    role_path = os.path.join(roles_dir, role_name)

    port = False
    varname = f'prometheus_role_exporter_port_{role_name}'

    # Check if defaults/main.yml exists
    defaults_path = os.path.join(role_path, 'defaults', 'main.yml')
    if os.path.exists(defaults_path):
        with open(defaults_path, 'r') as file:
            defaults_data = yaml.safe_load(file)
            result = defaults_data.get(varname)
            if result is not None:
                port = result 

    # Check if vars/main.yml exists
    vars_path = os.path.join(role_path, 'vars', 'main.yml')
    if os.path.exists(vars_path):
        with open(vars_path, 'r') as file:
            vars_data = yaml.safe_load(file)
            result = vars_data.get(varname)
            if result is not None:
                port = result 

    # Check if group_vars/main.yml exists
    group_vars_path = os.path.join(inventory_dir, 'group_vars', f'{role_name}.yml')
    if os.path.exists(group_vars_path):
        with open(group_vars_path, 'r') as file:
            vars_data = yaml.safe_load(file)
            result = vars_data.get(varname)
            if result is not None:
                port = result 

    return port  # Return None if the value is not found

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        inventory_dir=dict(type='str', required=True),
        roles_dir=dict(type='str', required=True)
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )


    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    # result['params'] = module.params
    all_roles = next(os.walk(module.params['roles_dir']))[1]
    result['all_roles'] = all_roles

    first_level_dependencies = get_all_dependencies(all_roles, module.params['roles_dir'])
    result['direct_dependencies'] = first_level_dependencies

    dependency_map = {}

    for role_name in all_roles:
        dependent_roles = list_dependent_roles(role_name, all_roles, first_level_dependencies)
        exporter_port = get_prometheus_exporter_port(role_name, module.params['roles_dir'], module.params['inventory_dir'])
        dependency_map[role_name] = { 
            "dependent_roles": dependent_roles,
            "exporter_port": exporter_port
        }

    result['dependency_map'] = dependency_map

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()