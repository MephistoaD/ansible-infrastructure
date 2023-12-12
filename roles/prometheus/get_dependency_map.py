#!/usr/bin/env python3

import json
import os
import yaml
import argparse



# wenn rolle a dependency von rolle b ist, 
# dann muss rolle b als dependent on rolle a gelistet werden

def list_dependent_roles(role_name):
    dependent_roles = set()

    stack = [role_name]
    while stack:
        current_role = stack.pop()
        dependent_roles.add(current_role)
        for role in ALL_ROLES:
            for dependency in DEPENDENCIES.get(role, []):
                if dependency == current_role:
                    stack.append(role)

    return list(dependent_roles)

def get_all_dependencies():
    all_dependencies = {}
    for role in ALL_ROLES:
        all_dependencies[role] = get_dependencies(role)
    return all_dependencies

def get_dependencies(role_name):
    dependencies = []

    meta_file = os.path.join(ROLES_DIR, role_name, 'meta', 'main.yml')

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

def get_prometheus_exporter_port(role_name, inventory_dir):
    role_path = os.path.join(ROLES_DIR, role_name)

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
            result = defaults_data.get(varname)
            if result is not None:
                port = result 

    # Check if hostvars/main.yml exists
    group_vars_path = os.path.join(inventory_dir, 'group_vars', f'{role_name}.yml')
    if os.path.exists(group_vars_path):
        with open(group_vars_path, 'r') as file:
            vars_data = yaml.safe_load(file)
            result = defaults_data.get(varname)
            if result is not None:
                port = result 

    return port  # Return None if the value is not found

# The dependecy map lists each role togehter with the roles it depends on, eg. nginx -> debian
def generate_dependency_map(inventory_dir):
    dependency_map = {}

    for role_name in ALL_ROLES:
        dependent_roles = list_dependent_roles(role_name)
        exporter_port = get_prometheus_exporter_port(role_name, inventory_dir)
        dependency_map[role_name] = { 
            "dependent_roles": dependent_roles,
            "exporter_port": exporter_port
        }


    return dependency_map

def main():
    parser = argparse.ArgumentParser(description='Example script with a command-line argument.')
    parser.add_argument('--inventory', required=True, help='Specify the path of the inventory file')
    args = parser.parse_args()
    inventory_dir = args.inventory

    dependency_map = generate_dependency_map(inventory_dir)

    print(json.dumps(dependency_map, indent=4))



####################
# globals:
ROLES_DIR = os.path.join(os.path.dirname(__file__), '..')
ALL_ROLES = next(os.walk(ROLES_DIR))[1]
DEPENDENCIES = get_all_dependencies()
####################

if __name__ == "__main__":
    main()
