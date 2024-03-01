#!/usr/bin/python3

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: semaphore_view

short_description: Manage views in semaphore

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: Create, list or delete views in ansible semaphore.

        api_endpoint=dict(type='str', required=True),
        api_token=dict(type='str', required=True),
        project=dict(type='str', required=True),
        name=dict(type='str', required=True),
        position=dict(type='int', required=False),
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
        description: The name of the view.
        required: true
        type: str
    position:
        description: The position (from left to right) where the view should be placed.
        required: false
        type: int
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
- name: Create view 'updates'
  semaphore_view:
    api_endpoint: "http://localhost:3000"
    api_token: "{{ admin_user.api_token }}"
    name: "updates"
    project: "my-project"
    position: 5

- name: Delete view 'updates'
  semaphore_view:
    api_endpoint: "http://localhost:3000"
    api_token: "{{ admin_user.api_token }}"
    name: "updates"
    project: "my-project"
    state: absent
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.

msg:
    description: A human-readable description of the changes done
    type: str
    returned: change
    sample: "Updated viev 'updates'"
views:
    description: The views currently set in this project.
    type: dict
    returned: always
    sample: [
            {
                "id": 1,
                "project_id": 1,
                "title": "setup",
                "position": 0
            },
            {
                "id": 2,
                "project_id": 1,
                "title": "upgrade",
                "position": 1
            },
            {
                "id": 3,
                "project_id": 1,
                "title": "other",
                "position": 3
            }
        ]
'''

from ansible.module_utils.basic import AnsibleModule

import requests
import json


def create_view(target_view, api_endpoint, api_token):
    url = f"{api_endpoint}/api/project/{target_view['project_id']}/views"
    headers = {
        "Authorization": f"Bearer {api_token}"
    }
    body = target_view
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

def modify_view(target_view, current_view_id, api_endpoint, api_token):
    url = f"{api_endpoint}/api/project/{target_view['project_id']}/views/{current_view_id}"
    headers = {
        "Authorization": f"Bearer {api_token}"
    }
    body = target_view
    body['id'] = current_view_id
    response = requests.put(url, headers=headers, json=body, verify=False)

    if (response.status_code // 100) != 2: # check if it's not in the 200 range
        error_message = response.content  # Assuming the content is in UTF-8 encoding
        raise Exception(f"Error {response.status_code}: {error_message}")

    # return response.json() # There is no body as answer

def delete_view(existing_view, api_endpoint, api_token):
    url = f"{api_endpoint}/api/project/{existing_view['project_id']}/views/{existing_view['id']}"
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
        position=dict(type='int', required=False),
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
    view = get_with(
                        location=f"/project/{project_id}/views", 
                        name=module.params['name'],
                        name_field="title",
                        api_endpoint=api_endpoint,
                        api_token=api_token
                    )
    
    #print(json.dumps(view))

    if module.params['state'] == "present" and 'position' in module.params:
        target_view = {
                "project_id": project_id,
                "title": module.params['name'],
                "position": module.params['position']
            }

        #print(json.dumps(target_view))

        # Create a new view
        if not view:
            create_view(
                target_view=target_view,
                api_endpoint=api_endpoint,
                api_token=api_token
            )
            result['msg'] = f"Created view '{module.params['name']}'"
            result['changed'] = True

        # Update a view
        elif not all(item in view.items() for item in target_view.items()):
            modify_view(
                target_view=target_view,
                current_view_id=view['id'],
                api_endpoint=api_endpoint,
                api_token=api_token
            )
            result['msg'] = f"Updated view '{target_view['title']}'"
            result['changed'] = True
        
    # Delete a view
    elif module.params['state'] == "absent" and view:
        delete_view(
            existing_view=view,
            api_endpoint=api_endpoint,
            api_token=api_token
        )
        result['msg'] = f"Deleted view '{view['title']}'"
        result['changed'] = True

    # Get updated schedule
    views = get_with(
                        location=f"/project/{project_id}/views", 
                        api_endpoint=api_endpoint,
                        api_token=api_token
                    )
    for view in views:
        view['name'] = view['title']
        view.pop('title')

    result['views'] = views

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()