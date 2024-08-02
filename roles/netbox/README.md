# Docker NetBox

This is one of the more complicated roles.

Take the NetBox host as a zygote for the permanent inventory.

## How To install

The first execution of the deployment playbook most likely fails.
Why? Well, the database migration of the NetBox installer takes longer than the houskeeping and rq-worker services are patient. As a consecuence they fail on their first execution, but recover by themselves as soon as the NetBox itself starts.

The second deployment needs to fail as well, but ends with a message, asking you to add an API-Token.

1. Create a superuser by logging into the shell of the NetBox instance and running `netbox-manage createsuperuser`
2. Log into the Webinterface of the NetBox instance and create a API-Token with write access.
3. Add the Token in `/etc/ansible/facts.d/netbox.fact` of the netbox instance 

Afterwards this playbook is capable of interacting with the netbox API as well. (Yes, sadly the deployment needs to be restarted a third time again.)
Future deployment runs however can be expected to perform successfully at the first try.

## How to add devices

Take a look at `inventory/yaml/sample_pve_host.yml`. There you'll find an example of a Inventory file suitable for usage in the `playbooks/add_phisical_to_netbox.yml`. You may trigger it as follwos:

```
ansible-playbook playbooks/add_phisical_to_netbox.yml -i inventory/yaml/ -e netbox_api_token=101ef77478bf0670a1314cc0504511490ee0bd01 -e target="pvehostname"
```
