#!/usr/bin/python3

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: semaphore_task_schedule

short_description: Manage task schedules in semaphore

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: Create, list or delete task schedules in ansible semaphore.

        api_endpoint=dict(type='str', required=True),
        api_token=dict(type='str', required=True),
        project=dict(type='str', required=True),
        task_template=dict(type='str', required=True),
        schedule=dict(type='str', required=False),
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
    task_template:
        description: The name of the task template.
        required: true
        type: str
    schedule:
        description: The schedule in cron syntax.
        required: false
        type: str
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
- name: Schedule tasks
  semaphore_task_schedule:
    api_endpoint: "http://localhost:3000"
    api_token: "xxxx"
    task_template: "Run Updates"
    project: "administration"
    schedule: "0 0 * * *"

- name: Unschedule tasks
  semaphore_task_schedule:
    api_endpoint: "http://localhost:3000"
    api_token: "xxxx"
    task_template: "Run Updates"
    project: "administration"
    state: absent
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.

msg:
    description: A human-readable description of the changes done
    type: str
    returned: change
    sample: "Updated schedule '1 1 1 * *' -> '0 * * * *' for task 'Run Updates'"
schedule:
    description: The schedule currently set for the task.
    type: dict
    returned: always
    sample: [
            {
                "id": 8,
                "project_id": 10,
                "template_id": 23,
                "cron_format": "0 * * * *",
                "repository_id": null
            }
        ]
'''

from ansible.module_utils.basic import AnsibleModule

import requests
import json


def create_schedule(target_schedule, api_endpoint, api_token):
    url = f"{api_endpoint}/api/project/{target_schedule['project_id']}/schedules"
    headers = {
        "Authorization": f"Bearer {api_token}"
    }
    body = target_schedule
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
        # print(json.dumps(next(iter(response_body), None)))
        return next(iter(response_body), None)

def modify_schedule(target_schedule, current_schedule_id, api_endpoint, api_token):
    url = f"{api_endpoint}/api/project/{target_schedule['project_id']}/schedules/{current_schedule_id}"
    headers = {
        "Authorization": f"Bearer {api_token}"
    }
    body = target_schedule
    body['id'] = current_schedule_id
    response = requests.put(url, headers=headers, json=body, verify=False)

    if (response.status_code // 100) != 2: # check if it's not in the 200 range
        error_message = response.content  # Assuming the content is in UTF-8 encoding
        raise Exception(f"Error {response.status_code}: {error_message}")

    # return response.json() # There is no body as answer

def delete_schedule(existing_schedule, api_endpoint, api_token):
    url = f"{api_endpoint}/api/project/{existing_schedule['project_id']}/schedules/{existing_schedule['id']}"
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
        task_template=dict(type='str', required=True),
        schedule=dict(type='str', required=False),
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
    task_template_id = get_with(
                        location=f"/project/{project_id}/templates", 
                        name=module.params['task_template'],
                        field='id',
                        api_endpoint=api_endpoint,
                        api_token=api_token
                    )
    schedule = get_with(
                        location=f"/project/{project_id}/templates/{task_template_id}/schedules", 
                        api_endpoint=api_endpoint,
                        api_token=api_token
                    )

    if module.params['state'] == "present" and 'schedule' in module.params:
        target_schedule = {
                "project_id": project_id,
                "template_id": task_template_id,
                "cron_format": module.params['schedule'],
                "repository_id": None # Why does the api require this?
            }
        #print(json.dumps(target_schedule))

        # Create a new schedule
        if schedule is None:
            create_schedule(
                target_schedule=target_schedule,
                api_endpoint=api_endpoint,
                api_token=api_token
            )
            result['msg'] = f"Created schedule '{module.params['schedule']}' for task '{module.params['task_template']}'"
            result['changed'] = True

        # Update a schedule
        elif schedule['cron_format'] != target_schedule['cron_format']:
            modify_schedule(
                target_schedule=target_schedule,
                current_schedule_id=schedule['id'],
                api_endpoint=api_endpoint,
                api_token=api_token
            )
            result['msg'] = f"Updated schedule '{schedule['cron_format']}' -> '{module.params['schedule']}' for task '{module.params['task_template']}'"
            result['changed'] = True
        
    # Delete a schedule
    elif module.params['state'] == "absent" and schedule is not None:
        delete_schedule(
            existing_schedule=schedule,
            api_endpoint=api_endpoint,
            api_token=api_token
        )
        result['msg'] = f"Deleted schedule '{schedule['cron_format']}' for task '{module.params['task_template']}'"
        result['changed'] = True

    # Get updated schedule
    if result['changed']:
        schedule = get_with(
                        location=f"/project/{project_id}/templates/{task_template_id}/schedules", 
                        api_endpoint=api_endpoint,
                        api_token=api_token
                    )

    result['schedule'] = schedule

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()