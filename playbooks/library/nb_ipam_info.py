#!/usr/bin/python3

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: nb_ipam_info

short_description: Returns all IPAM Data from NetBox

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: An Info module returning IP-Addresses, IP-Ranges and the ips for each host.

        api_endpoint=dict(type='str', required=True),
        token=dict(type='str', required=True),
        validate_certs=dict(type='bool', required=False, default=True)

options:
    api_endpoint:
        description: The URL to the NetBox API.
        required: true
        type: str
    token:
        description: The API token for the NetBox instance (read only permissions should be sufficient)
        required: true
        type: str
    validate_certs:
        description: 
            Wether to validate the SSL certificate of the NetBox server.
            options:
            - True (defualt)
            - False
        required: false
        type: bool
# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
# extends_documentation_fragment:
#     - my_namespace.my_collection.my_doc_fragment_name

author:
    - MephistoaD (@MephistoaD)
'''

EXAMPLES = r'''
- name: Get all IPAM info
  nb_ipam_info:
    api_endpoint: "https://netbox.local"
    token: "xxxyyy"
    validate_certs: False
  register: ipam_info
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.

addresses:
    description: A list containing all known IP-Addresses.
    type: dict
    returned: always
    sample: {
            "10.0.0.2/24": {
                "address": "10.0.0.2/24",
                "custom_fields": {},
                "description": "",
                "dns_name": "webserver.local",
                "instance": "webserver",
                "interface": "eth0",
                "tags": []
            },
        }
instances:
    description: A list of the interfaces and their IP-addresses per interface.
    type: dict
    returned: always
    sample: {
        "webserver": {
                "eth0": [
                    "10.0.0.2/24"
                ],
                "wg0": [
                    "10.1.1.1/24"
                ]
            }
        }
ranges:
    description: A list of all known IP-ranges and their IP addresses.
    type: list
    returned: always
    sample: [
            {
                "addresses": [
                    "10.0.0.2/24"
                ],
                "comments": "",
                "custom_fields": {},
                "description": "local network",
                "display": "10.0.0.1-254/24",
                "end_address": "10.0.0.254/24",
                "family": {
                    "label": "IPv4",
                    "value": 4
                },
                "role": null,
                "size": 254,
                "start_address": "10.0.0.1/24",
                "tags": [],
                "vrf": null
            }
            ]
'''

from ansible.module_utils.basic import AnsibleModule

import requests
import json
import ipaddress


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        api_endpoint=dict(type='str', required=True),
        token=dict(type='str', required=True),
        validate_certs=dict(type='bool', required=False, default=True)
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

    api_endpoint = f"{module.params['api_endpoint']}{'/' if not module.params['api_endpoint'].endswith('/') else ''}"
    verify = False #module.params['validate_certs']
    ip_ranges_url = f"{api_endpoint}api/ipam/ip-ranges/"
    ip_addresses_url = f"{api_endpoint}api/ipam/ip-addresses/"
    headers = {"Authorization": f"Token {module.params['token']}"}

    ip_ranges_raw = requests.get(ip_ranges_url, headers=headers, verify=verify)
    ip_addresses_raw = requests.get(ip_addresses_url, headers=headers, verify=verify)

    ip_ranges = json.loads(ip_ranges_raw.text)['results']
    ip_addresses = json.loads(ip_addresses_raw.text)['results']
    
    instances = {}
    addresses = {}
    for ip_address in ip_addresses:
        if ip_address['status']['value'] != "active":
            ip_addresses.remove(ip_address)
            continue

        addresses[ip_address['address']] = {
            'address': ip_address['address'],
            'custom_fields': ip_address['custom_fields'],
            'description': ip_address['description'],
            'dns_name': ip_address['dns_name'],
            'tags': ip_address['tags'],
        }

        if ip_address['assigned_object'] is not None:
            # interface = interface name
            addresses[ip_address['address']]['interface'] = ip_address['assigned_object']['name']
            # instance = name if connected device or vm
            addresses[ip_address['address']]['instance'] = ip_address['assigned_object'][f"{ 'device' if 'device' in ip_address['assigned_object'] else 'virtual_machine'}"]['name']

        # nat_inside is the nat the current ip is on the inside of
        if ip_address['nat_inside'] is not None:
            addresses[ip_address['address']]['nat_inside'] = ip_address['nat_inside']['address']

        # nat_outside is the list of nat addresses inside of this ip
        if len(ip_address['nat_outside']) > 0:
            addresses[ip_address['address']]['nat_outside'] = [ outside['address'] for outside in ip_address['nat_outside'] ]

        host_type = f"{'virtual_machine' if 'virtual_machine' in ip_address['assigned_object'] else 'device'}"
        if (ip_address['assigned_object'] is not None and 
            host_type in ip_address['assigned_object']):
            print(ip_address['assigned_object'][host_type]['name'])
            if ip_address['assigned_object'][host_type]['name'] not in instances:
                instances[ip_address['assigned_object'][host_type]['name']] = {}
                print("added dict")
            if ip_address['assigned_object']['name'] not in instances[ip_address['assigned_object'][host_type]['name']]:
                instances[ip_address['assigned_object'][host_type]['name']][ip_address['assigned_object']['name']] = []
            instances[ip_address['assigned_object'][host_type]['name']][ip_address['assigned_object']['name']].append(ip_address['address'])

    result['instances'] = instances
    result['addresses'] = addresses

    ranges = {}
    for ip_range in ip_ranges:
        if ip_range['status']['value'] != "active":
            ip_range.remove(ip_address)
            continue

        ranges[ip_range['start_address']] = ip_range

        # the range itself
        for field in ['url', 'created', 'last_updated', 'id', 'tenant', 'status']:
            ip_range.pop(field)

        ip_range['addresses'] = []
        ip_segments = ip_range['start_address'].split('.')
        network = ipaddress.ip_network(f"{ip_segments[0]}.{ip_segments[1]}.{ip_segments[2]}.0/{ip_segments[3].split('/')[-1]}")
        for address in addresses:
            ip = ipaddress.ip_address(addresses[address]['address'].split("/")[0])
            if ip in network:
                ip_range['addresses'].append(addresses[address]['address'])
                addresses[address]['gateway'] = ip_range['start_address']

    for range in ranges.values():

        for address in range['addresses']:
            if 'wg' in addresses[address]['interface']:
                if address == addresses[address]['gateway']:
                    addresses[address]['peers'] = [
                            addr for addr in range['addresses'] if addr != address
                        ]
                else:
                    addresses[address]['peers'] = [
                            addresses[address]['gateway']
                        ]
                                             
    result['ranges'] = ranges

    vpn_peers = {}
    for address in addresses.values():
        if 'peers' in address:
            if address['instance'] not in vpn_peers:
                vpn_peers[address['instance']] = []
            for peer in address['peers']:
                peer = addresses[peer]['instance']
                vpn_peers[address['instance']].append(peer)
        
    result['vpn_peers'] = vpn_peers

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()