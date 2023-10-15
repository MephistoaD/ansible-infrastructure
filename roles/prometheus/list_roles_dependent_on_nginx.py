import json
import os
import yaml

# globals:
ROLES_DIR = os.path.join(os.path.dirname(__file__), '..')
ALL_ROLES = next(os.walk(ROLES_DIR))[1]
####################


def list_dependent_roles(role_name):
    dependent_roles = [ role_name ]

    all_dependencies = get_all_dependencies()

    dependent_count = 0

    while dependent_count < len(dependent_roles):
        dependent_count = len(dependent_roles)
        added = []
        for current_role in dependent_roles:
            added.extend([ role for role in all_dependencies if current_role in get_dependencies(role) ])
        dependent_roles.extend(added)
        dependent_roles = list(set(dependent_roles))
    
    return dependent_roles

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
                dependencies = [ d['role'] for d in dependencies_raw]
    except:
        pass
    
    return dependencies

dependent_roles = list_dependent_roles("nginx")

print(json.dumps(dependent_roles, indent=4))
