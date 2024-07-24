#!/usr/bin/python3

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: prometheus_dependency_map_info

short_description: Returns a map from each role on the roles depending on it.

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: |
    Returns a map of each locally available ansible role resolving to a list of roles 
    which are including it. Additionally it returns the port each role-dedicated 
    prometheus exporter is running on, or false.

        inventory_dir=dict(type='str', required=True),
        roles_dir=dict(type='str', required=True),

options:
    inventory_dir:
        description: The directory of the current inventory
        required: true
        type: str
    roles_dir:
        description: The directory of the current roles
        required: true
        type: str
# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
# extends_documentation_fragment:
#     - my_namespace.my_collection.my_doc_fragment_name

author:
    - MephistoaD (@MephistoaD)
'''

EXAMPLES = r'''
- name: Get dependency map
  become: false
  local_action:
    module: prometheus_dependency_map_info
    inventory_dir: "{{ inventory_dir }}"
    roles_dir: "{{ playbook_dir }}/../roles"
  register: role_dependencies
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.

all_roles:
    description: A list containing all known roles.
    type: list
    returned: always
    sample: [
            nginx,
            prometheus
        ]
dependencies:
    description: A direct mapping from each role to it's first level dependencies.
    type: dict
    returned: always
    sample: {
        "nginx" [],
        "prometheus": [
                "nginx"
            ]
        }
dependency_map:
    description: The full map of each role to all of the roles depending on it.
    type: list
    returned: always
    sample: {
            "nginx": {
                "dependent_roles": [
                    "nginx",
                    "prometheus"
                ],
                "exporter_port": 9113,
                "exporter_path": "/metrics"
            },
            "prometheus": {
                "dependent_roles": [
                    "prometheus"
                ],
                "exporter_port": false,
                "exporter_path": false
            }
        }
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

    # direct dependencies via ansible
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

    # dependencies via prometheus role from defaults/main.yml
    defaults_file = os.path.join(roles_dir, role_name, 'defaults', 'main.yml')
    try:
        if os.path.exists(defaults_file):
            with open(defaults_file, 'r') as f:
                default_vars = yaml.safe_load(f)
                prometheus_roles = default_vars.get('prometheus_roles', [])

                # Check if the specified role_name is in the dependencies
                for r in prometheus_roles:
                    if isinstance(r, dict):
                        dependencies.append(r['role'])
                    elif isinstance(r, str):
                        dependencies.append(r)
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

def get_prometheus_exporter_path(role_name, roles_dir, inventory_dir):
    role_path = os.path.join(roles_dir, role_name)

    extracted_path = False
    varname = f'prometheus_role_exporter_path_{role_name}'

    # Check if defaults/main.yml exists
    defaults_path = os.path.join(role_path, 'defaults', 'main.yml')
    if os.path.exists(defaults_path):
        with open(defaults_path, 'r') as file:
            defaults_data = yaml.safe_load(file)
            result = defaults_data.get(varname)
            if result is not None:
                extracted_path = result 

    # Check if vars/main.yml exists
    vars_path = os.path.join(role_path, 'vars', 'main.yml')
    if os.path.exists(vars_path):
        with open(vars_path, 'r') as file:
            vars_data = yaml.safe_load(file)
            result = vars_data.get(varname)
            if result is not None:
                extracted_path = result 

    # Check if group_vars/main.yml exists
    group_vars_path = os.path.join(inventory_dir, 'group_vars', f'{role_name}.yml')
    if os.path.exists(group_vars_path):
        with open(group_vars_path, 'r') as file:
            vars_data = yaml.safe_load(file)
            result = vars_data.get(varname)
            if result is not None:
                extracted_path = result 

    return extracted_path  # Return None if the value is not found

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
        exporter_path = get_prometheus_exporter_path(role_name, module.params['roles_dir'], module.params['inventory_dir'])
        
        dependency_map[role_name] = { 
            "dependent_roles": dependent_roles,
            "exporter_port": exporter_port,
            "exporter_path": exporter_path
        }

    result['dependency_map'] = dependency_map

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()