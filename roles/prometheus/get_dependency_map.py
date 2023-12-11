import json
import os
import yaml



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

# The dependecy map lists each role togehter with the roles it depends on, eg. nginx -> debian
def generate_dependency_map():
    dependency_map = {}

    for role_name in ALL_ROLES:
        dependent_roles = list_dependent_roles(role_name)
        dependency_map[role_name] = dependent_roles

    return dependency_map

def main():
    dependency_map = generate_dependency_map()

    print(json.dumps(dependency_map, indent=4))

####################
# globals:
ROLES_DIR = os.path.join(os.path.dirname(__file__), '..')
ALL_ROLES = next(os.walk(ROLES_DIR))[1]
DEPENDENCIES = get_all_dependencies()
####################

if __name__ == "__main__":
    main()
