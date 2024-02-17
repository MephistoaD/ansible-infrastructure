#!/usr/bin/python3

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: github_latest_release_info

short_description: Returns a list of all releases available for a github repository.

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: |
    Returns a list of all releases available for a github repository.

        upstream_repo=dict(type='str', required=True)

options:
    upstream_repo:
        description: The URL to the repository.
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
- name: Get prometheus releases
  github_latest_release_info:
    upstream_repo: https://github.com/prometheus/alertmanager
  register: prometheus_releases

- name: Get prometheus releases
  become: false
  local_action:
    module: github_latest_release_info
    upstream_repo: prometheus/alertmanager
  register: prometheus_releases
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.

latest_release:
    description: The version of the latest release.
    type: str
    returned: always
    sample: "0.26.0"
releases:
    description: A dict mapping the releases to the download addresses
    type: dict
    returned: always
    sample: {
            "0.16.0": {
                "tarball_url": "https://api.github.com/repos/prometheus/alertmanager/tarball/v0.16.0",
                "zipball_url": "https://api.github.com/repos/prometheus/alertmanager/zipball/v0.16.0"
            },
            "0.16.0-alpha.0": {
                "tarball_url": "https://api.github.com/repos/prometheus/alertmanager/tarball/v0.16.0-alpha.0",
                "zipball_url": "https://api.github.com/repos/prometheus/alertmanager/zipball/v0.16.0-alpha.0"
            }
        }
'''

from ansible.module_utils.basic import AnsibleModule

import requests


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        upstream_repo=dict(type='str', required=True)
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
    repo = module.params['upstream_repo'].split('https://github.com')[-1].strip('/')

    # GitHub repository and API endpoint
    api_url = f"https://api.github.com/repos/{ repo }"
    releases_url = f"{ api_url }/releases"
    latest_url = f"{ api_url }/releases/latest"

    # Get the latest release version using requests and json
    response = requests.get(latest_url)
    data = response.json()
    result['latest_release'] = data.get("tag_name").strip('v')

    # Get the download addresses for all releases
    response = requests.get(releases_url)
    data = response.json()
    releases = {}
    for release in data:
        releases[release.get("tag_name").strip('v')] = {
            "tarball_url": release.get("tarball_url"),
            "zipball_url": release.get("zipball_url")
        }
    result['releases'] = releases

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()