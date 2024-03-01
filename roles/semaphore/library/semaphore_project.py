#!/usr/bin/python3

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: semaphore_project

short_description: Manage projects in semaphore

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: Create, list or delete projects in ansible semaphore.

        api_endpoint=dict(type='str', required=True),
        api_token=dict(type='str', required=True),
        project=dict(type='dict', required=False),
        state=dict(type='str', required=False, default="present"),

options:
    api_endpoint:
        description: The URL to the Semaphore API.
        required: true
        type: str
    api_token:
        description: The API token for the Semaphore instance
        required: true
        type: str
    project:
        description: The project configuration.
        required: false
        type: str
# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
# extends_documentation_fragment:
#     - my_namespace.my_collection.my_doc_fragment_name

author:
    - MephistoaD (@MephistoaD)
'''

EXAMPLES = r'''
- name: "Configure project '{{ project.name }}'"
  semaphore_project:
    api_endpoint: "http://localhost:3000"
    api_token: "xxx"
    project:
      name: "automations"
      alert: false
      alert_chat: ''
      max_parallel_tasks: "0"
    state: present
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.

msg:
    description: A human-readable description of the changes done
    type: str
    returned: change
    sample: "Removed project automations"
projects:
    description: A list of the projects, existing within the semaphore instance.
    type: list
    returned: always
    sample: [
            {
                "alert": false,
                "alert_chat": "",
                "created": "2024-02-17T12:11:01.06664Z",
                "id": 1,
                "max_parallel_tasks": 7,
                "name": "automations"
            },
            {
                "alert": false,
                "alert_chat": null,
                "created": "2024-02-21T20:53:05.421544Z",
                "id": 8,
                "max_parallel_tasks": 4,
                "name": "deployments"
            }
        ]
'''

from ansible.module_utils.basic import AnsibleModule

import requests

def align_data(project):
    project['max_parallel_tasks'] = int(project['max_parallel_tasks'])

def create_project(project, api_endpoint, api_token):
    url = f"{api_endpoint}/api/projects"
    headers = {
        "Authorization": f"Bearer {api_token}"
    }
    body = project
    response = requests.post(url, headers=headers, json=body, verify=False)

    if (response.status_code // 100) != 2: # check if it's not in the 200 range
        error_message = response.content  # Assuming the content is in UTF-8 encoding
        raise Exception(f"Error {response.status_code}: {error_message}")

    return response.json()

def get_projects(api_token, api_endpoint):
    url = f"{api_endpoint}/api/projects"
    headers = {
        "Authorization": f"Bearer {api_token}"
    }
    response = requests.get(url, headers=headers, verify=False)
    return response.json()

def get_project_from_list(project_name, current_projects) -> dict:
    for project in current_projects:
        if project['name'] == project_name:
            return project
    return None

def modify_project(project, to_project_id, api_endpoint, api_token):
    url = f"{api_endpoint}/api/project/{to_project_id}"
    headers = {
        "Authorization": f"Bearer {api_token}"
    }
    body = project
    body['id'] = to_project_id
    response = requests.put(url, headers=headers, json=body, verify=False)

    if (response.status_code // 100) != 2: # check if it's not in the 200 range
        error_message = response.content  # Assuming the content is in UTF-8 encoding
        raise Exception(f"Error {response.status_code}: {error_message}")

    # return response.json() # There is no body as answer

def project_does_not_match_fields_from(project, fields) -> bool:
    for key, value in fields.items():
        if key not in project or value != project[key]:
            return True
    return False

def project_is_valid(project) -> bool:
    return (
            'name' in project
        )

def remove_project(project_id, api_endpoint, api_token):
    url = f"{api_endpoint}/api/project/{project_id}"
    headers = {
        "Authorization": f"Bearer {api_token}"
    }
    response = requests.delete(url, headers=headers, verify=False)

    if (response.status_code // 100) != 2: # check if it's not in the 200 range
        error_message = response.content  # Assuming the content is in UTF-8 encoding
        raise Exception(f"Error {response.status_code}: {error_message}")

    # return response.json() # There is no body as answer

def sync_project(result, module, api_token, api_endpoint):
    project = module.params['project']
    current_projects = get_projects(
                                api_endpoint=api_endpoint,
                                api_token=api_token
                            )
    existing_project = get_project_from_list(
                                project_name=project['name'], 
                                current_projects=current_projects
                            )
        
    if module.params['state'] == "present":
        if existing_project is None: # Add project
            if not module.check_mode:
                res = create_project(
                            project=project,
                            api_endpoint=api_endpoint,
                            api_token=api_token
                        )
                result['response'] = res
            result['msg'] = f"Created project {project['name']}"
            result['changed'] = True
        elif project_does_not_match_fields_from(existing_project, project): # Modify project
            if not module.check_mode:
                modify_project(
                            project=project,
                            to_project_id=existing_project['id'],
                            api_endpoint=api_endpoint,
                            api_token=api_token
                        )
            result['msg'] = f"Modified project {project['name']}"
            result['changed'] = True
    elif existing_project is not None: # Remove project
        if not module.check_mode:
            remove_project(
                        project_id=existing_project['id'],
                        api_endpoint=api_endpoint,
                        api_token=api_token
                    )
            result['msg'] = f"Removed project {project['name']}"
            result['changed'] = True

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        api_endpoint=dict(type='str', required=True),
        api_token=dict(type='str', required=True),
        project=dict(type='dict', required=False),
        state=dict(type='str', required=False, default="present"),
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

    api_token = module.params['api_token']
    api_endpoint = module.params['api_endpoint']

    if module.params['project'] is not None and project_is_valid(module.params['project']):
        align_data(module.params['project'])
        sync_project(result, module, api_token, api_endpoint)


    projects = get_projects(api_token, api_endpoint)
    result['projects'] = projects


    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()