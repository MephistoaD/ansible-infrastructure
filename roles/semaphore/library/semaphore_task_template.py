#!/usr/bin/python3

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: semaphore_task_template

short_description: Manage task templates in semaphore

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: Create, list or delete task_templates in ansible semaphore.

        api_endpoint=dict(type='str', required=True),
        api_token=dict(type='str', required=True),
        name=dict(type='str', required=True),
        environment=dict(type='str', required=True),
        description=dict(type='str', required=False),
        inventory=dict(type='str', required=True),
        playbook=dict(type='str', required=True),
        project=dict(type='str', required=True),
        repository=dict(type='str', required=True),
        view=dict(type='str', required=False),
        vars=dict(type='list', required=False),
        state=dict(type='str', required=False, default="present"),

options:
    api_endpoint:
        description: The URL to the Semaphore API.
        required: false
        type: str
    api_token:
        description: The API token for the Semaphore instance
        required: true
        type: str
    name:
        description: The name of the task_template.
        required: true
        type: str
    environment:
        description: The name of the related environment.
        required: true
        type: str
    description:
        description: The description of the task_template.
        required: true
        type: str
    inventory:
        description: The name of the related inventory.
        required: true
        type: str
    repository:
        description: The name of the related repository.
        required: true
        type: str
    playbook:
        description: The relative path of the playbook within the repository.
        required: true
        type: str
    project:
        description: The name of the related project.
        required: true
        type: str
    view:
        description: The name of the related view.
        required: false
        type: str
    vars:
        description: The survey_vars in api-compatible format.
        required: false
        type: str
    state:
        description: The desired presence / absence of the task template.
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
- name: Create task templates 'update host'
  semaphore_task_template:
    api_endpoint: "http://localhost:3000"
    api_token: "{{ admin_user.api_token }}"
    name: "update host"
    description: "updates a host" # optional
    project: "my-project"
    playbook: "playbooks/update_host.yml"
    inventory: "test-inventory"
    repository: "ansible-repository"
    environment: "default-env"
    view: "updates" # optional
    vars: # optional
      - name: "target"
        title: "Target (required)"
        description: "The target system or group of the playbook"
        type: "string"
        required: false

- name: Delete obsolete task template 'update host'
  semaphore_task_template:
    api_endpoint: "http://localhost:3000"
    api_token: "{{ admin_user.api_token }}"
    name: "update host"
    project: "my-project"
    playbook: "some"
    inventory: "ignored"
    repository: "data"
    environment: "lol"
    state: absent
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.

msg:
    description: A human-readable description of the changes done
    type: str
    returned: change
    sample: "Removed project automations"
task_templates:
    description: A list of the task_templates, existing within the project instance.
    type: list
    returned: always
    sample: [
            {
                "allow_override_args_in_task": true,
                "arguments": null,
                "autorun": false,
                "build_template_id": null,
                "description": null,
                "environment_id": 8,
                "id": 22,
                "inventory_id": 3,
                "last_task": null,
                "name": "Sample task",
                "playbook": "file",
                "project_id": 10,
                "repository_id": 5,
                "start_version": null,
                "suppress_success_alerts": false,
                "survey_vars": null,
                "type": "",
                "vault_key_id": null,
                "view_id": 7
            }
        ]
'''

from ansible.module_utils.basic import AnsibleModule

import requests
import json


def create_task_template(target_task_template, api_endpoint, api_token):
    url = f"{api_endpoint}/api/project/{target_task_template['project_id']}/templates"
    headers = {
        "Authorization": f"Bearer {api_token}"
    }
    body = target_task_template
    #print(json.dumps(body))
    response = requests.post(url, headers=headers, json=body, verify=False)

    if (response.status_code // 100) != 2: # check if it's not in the 200 range
        error_message = response.content  # Assuming the content is in UTF-8 encoding
        raise Exception(f"Error {response.status_code}: {error_message}")

    return response.json()

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
        # #print(json.dumps(next(iter(response_body), None)))
        return response_body

def modify_task_template(target_task_template, current_task_template_id, api_endpoint, api_token):
    url = f"{api_endpoint}/api/project/{target_task_template['project_id']}/templates/{current_task_template_id}"
    headers = {
        "Authorization": f"Bearer {api_token}"
    }
    body = target_task_template
    body['id'] = current_task_template_id
    response = requests.put(url, headers=headers, json=body, verify=False)

    if (response.status_code // 100) != 2: # check if it's not in the 200 range
        error_message = response.content  # Assuming the content is in UTF-8 encoding
        raise Exception(f"Error {response.status_code}: {error_message}")

    # return response.json() # There is no body as answer

def delete_task_template(existing_task_template, api_endpoint, api_token):
    url = f"{api_endpoint}/api/project/{existing_task_template['project_id']}/templates/{existing_task_template['id']}"
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
        name=dict(type='str', required=True),
        environment=dict(type='str', required=True),
        description=dict(type='str', required=False),
        inventory=dict(type='str', required=True),
        playbook=dict(type='str', required=True),
        project=dict(type='str', required=True),
        repository=dict(type='str', required=True),
        view=dict(type='str', required=False),
        vars=dict(type='list', required=False),
        state=dict(type='str', required=False, default="present"),
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        log=[],
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
    task_template_id = get_with(
                        location=f"/project/{project_id}/templates", 
                        name=module.params['name'],
                        field='id',
                        api_endpoint=api_endpoint,
                        api_token=api_token
                    ) # does not return the entire data :-(
    if task_template_id:
        task_template = get_with(
                        location=f"/project/{project_id}/templates/{task_template_id}",
                        api_endpoint=api_endpoint,
                        api_token=api_token
                    )
        task_template['app'] = "ansible"
    
        #print(json.dumps(task_template))

    result['log'].append("After initial get block")

    if module.params['state'] == "present":
        result['log'].append(f"Task template '{module.params['environment']}' already present")
        environment_id = get_with(
                        location=f"/project/{project_id}/environment", 
                        name=module.params['environment'],
                        field='id',
                        api_endpoint=api_endpoint,
                        api_token=api_token
                    )
        inventory_id = get_with(
                        name=module.params['inventory'],
                        field='id',
                        location=f"/project/{project_id}/inventory",
                        api_endpoint=api_endpoint,
                        api_token=api_token
                    )
        repository_id = get_with(
                        name=module.params['repository'],
                        field='id',
                        location=f"/project/{project_id}/repositories",
                        api_endpoint=api_endpoint,
                        api_token=api_token
                    )

        result['log'].append(f"Fetched additional IDs.")

        target_task_template = {
                "type": "",
                "project_id": project_id,
                "name": module.params['name'],
                "playbook": module.params['playbook'],
                "environment_id": environment_id,
                "inventory_id": inventory_id,
                "repository_id": repository_id,
                "app": "ansible"
            }
        
        if module.params['description'] is not None:
            target_task_template['description'] = module.params['description']
        if module.params['view'] is not None:
            result['log'].append(f"adding view parameter '{module.params['view']}'")
            target_task_template['view_id'] = get_with(
                        name=module.params['view'],
                        field='id',
                        name_field="title",
                        location=f"/project/{project_id}/views", 
                        api_endpoint=api_endpoint,
                        api_token=api_token
                    )
        if module.params['vars'] is not None:
            target_task_template['survey_vars'] = module.params['vars']
            for var in target_task_template['survey_vars']:
                if 'values' not in var:
                    var['values'] = None

        #print(json.dumps(target_task_template))

        result['body'] = target_task_template

        # Create a new task template
        if not task_template_id:
            create_task_template(
                target_task_template=target_task_template,
                api_endpoint=api_endpoint,
                api_token=api_token
            )
            result['msg'] = f"Created task template '{module.params['name']}'"
            result['changed'] = True

        # Update a task template
        elif not all(item in task_template.items() for item in target_task_template.items()):
            for item in target_task_template.items():
                result['log'].append(f"{item} -> {item in task_template.items()}")
            modify_task_template(
                target_task_template=target_task_template,
                current_task_template_id=task_template['id'],
                api_endpoint=api_endpoint,
                api_token=api_token
            )
            result['msg'] = f"Updated task template '{target_task_template['name']}'"
            result['changed'] = True
        
    # Delete a task_template
    elif module.params['state'] == "absent" and task_template:
        result['log'].append(f"Deleting Task template '{module.params['environment']}'")
        delete_task_template(
            existing_task_template=task_template,
            api_endpoint=api_endpoint,
            api_token=api_token
        )
        result['msg'] = f"Deleted task template '{task_template['name']}'"
        result['changed'] = True


    task_template_current_state = get_with(
                            location=f"/project/{project_id}/templates", 
                            api_endpoint=api_endpoint,
                            api_token=api_token
                        )
    result['task_templates'] = task_template_current_state

    result['log'].append("Finished successfully")


    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()