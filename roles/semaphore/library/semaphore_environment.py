#!/usr/bin/python3

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: semaphore_environment

short_description: Manage environments in semaphore

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: Create, list or delete environments in ansible semaphore.

        api_endpoint=dict(type='str', required=True),
        api_token=dict(type='str', required=True),
        project=dict(type='str', required=True),
        name=dict(type='str', required=True),
        vars=dict(type='dict', required=False),
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
        description: The project name.
        required: true
        type: str
    name:
        description: The name of the environment.
        required: true
        type: str
    vars:
        description: The variables stored in the environment.
        required: false
        type: dict
    state:
        description: The desired presece or absence of the entry.
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
- name: Create environment default
  semaphore_environment:
    api_endpoint: "http://localhost:3000"
    api_token: "{{ admin_user.api_token }}"
    name: "default"
    project: "my-project"
    vars: 
      key1: value
      key2: value

- name: Delete environment default-env
  semaphore_environment:
    api_endpoint: "http://localhost:3000"
    api_token: "{{ admin_user.api_token }}"
    name: "default-env"
    project: "my-project}"
    state: absent
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.

msg:
    description: A human-readable description of the changes done
    type: str
    returned: change
    sample: "Updated environment 'default-env'"
environments:
    description: The environments within the given project.
    type: list
    returned: always
    sample: [
            {
                "id": 2,
                "name": "Machine maintainance",
                "project_id": 1,
                "password": null,
                "json": "{\"upgrade\": true, \"deploy_guest\": true}",
                "env": null
            },
            {
                "id": 1,
                "name": "Setup machine",
                "project_id": 1,
                "password": null,
                "json": "{\"upgrade\": false, \"deploy_guest\": true}",
                "env": null
            }
        ]
'''

from ansible.module_utils.basic import AnsibleModule

import requests
import json


def create_environment(target_environment, api_endpoint, api_token):
    url = f"{api_endpoint}/api/project/{target_environment['project_id']}/environment"
    headers = {
        "Authorization": f"Bearer {api_token}"
    }
    body = target_environment
    response = requests.post(url, headers=headers, json=body, verify=False)

    if (response.status_code // 100) != 2: # check if it's not in the 200 range
        error_message = response.content  # Assuming the content is in UTF-8 encoding
        raise Exception(f"Error {response.status_code}: {error_message}")

    #return response.json()

def get_with(location, api_endpoint, api_token, name=False, field=False, name_field='name'):
    url = f"{api_endpoint}/api{location}"
    headers = {
        "Authorization": f"Bearer {api_token}"
    }
    response = requests.get(url, headers=headers, verify=False)

    if (response.status_code // 100) != 2: # check if it's not in the 200 range
        error_message = response.content  # Assuming the content is in UTF-8 encoding
        raise Exception(f"Error {response.status_code}: {error_message} on request against {url}")

    response_body = response.json()
    if name:
        for item in response_body:
            if item[name_field] == name:
                if field:
                    return item[field]
                else:
                    return item
        return False
    else:
        # print(json.dumps(next(iter(response_body), None)))
        return response_body

def modify_environment(target_environment, current_environment_id, api_endpoint, api_token):
    url = f"{api_endpoint}/api/project/{target_environment['project_id']}/environment/{current_environment_id}"
    headers = {
        "Authorization": f"Bearer {api_token}"
    }
    body = target_environment
    body['id'] = current_environment_id
    response = requests.put(url, headers=headers, json=body, verify=False)

    if (response.status_code // 100) != 2: # check if it's not in the 200 range
        error_message = response.content  # Assuming the content is in UTF-8 encoding
        raise Exception(f"Error {response.status_code}: {error_message}")

    # return response.json() # There is no body as answer

def delete_environment(existing_environment, api_endpoint, api_token):
    url = f"{api_endpoint}/api/project/{existing_environment['project_id']}/environment/{existing_environment['id']}"
    headers = {
        "Authorization": f"Bearer {api_token}"
    }
    response = requests.delete(url, headers=headers, verify=False)

    if (response.status_code // 100) != 2: # check if it's not in the 200 range
        error_message = response.content  # Assuming the content is in UTF-8 encoding
        raise Exception(f"Error {response.status_code}: {error_message}")

    # return response.json() # There is no body as answer

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        api_endpoint=dict(type='str', required=True),
        api_token=dict(type='str', required=True),
        project=dict(type='str', required=True),
        name=dict(type='str', required=True),
        vars=dict(type='dict', required=False),
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

    project_id = get_with(
                        location="/projects",
                        name=module.params['project'],
                        field='id',
                        api_endpoint=api_endpoint,
                        api_token=api_token
                    )
    environment = get_with(
                        location=f"/project/{project_id}/environment", 
                        name=module.params['name'],
                        api_endpoint=api_endpoint,
                        api_token=api_token
                    )

    if module.params['state'] == "present" and 'vars' in module.params:
        target_environment = {
                "project_id": project_id,
                "name": module.params['name'],
                "json": json.dumps(module.params['vars'])
            }

        #print(json.dumps(target_environment))

        # Create a new environment
        if not environment:
            create_environment(
                target_environment=target_environment,
                api_endpoint=api_endpoint,
                api_token=api_token
            )
            result['msg'] = f"Created environment '{module.params['name']}'"
            result['changed'] = True

        # Update an environment
        elif environment['json'] != target_environment['json']:
            modify_environment(
                target_environment=target_environment,
                current_environment_id=environment['id'],
                api_endpoint=api_endpoint,
                api_token=api_token
            )
            result['msg'] = f"Updated environment '{environment['json']}' -> '{target_environment['json']}'"
            result['changed'] = True
        
    # Delete a schedule
    elif module.params['state'] == "absent" and environment:
        delete_environment(
            existing_environment=environment,
            api_endpoint=api_endpoint,
            api_token=api_token
        )
        result['msg'] = f"Deleted environment '{environment['name']}'"
        result['changed'] = True

    # # Get updated schedule
    environments = get_with(
                        location=f"/project/{project_id}/environment", 
                        api_endpoint=api_endpoint,
                        api_token=api_token
                    )

    result['environments'] = environments

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()