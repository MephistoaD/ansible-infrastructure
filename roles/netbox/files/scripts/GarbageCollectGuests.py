from extras.scripts import *

from dcim.choices import VirtualDeviceContextStatusChoices
from virtualization.models import VirtualMachine, VMInterface
from ipam.models import IPAddress
from ipam.choices import IPAddressStatusChoices, IPAddressRoleChoices

import requests

class GarbageCollectGuests(Script):

    class Meta:
        name = "Garbage Collect Guests"
        description = "Remove all guests which are set to 'Decomissioning'"
        scheduling_enabled=True


    def run(self, data, commit):
        # get all guests to remove
        decommissioning = VirtualMachine.objects.filter(status='decommissioning')

        for guest in decommissioning:
            self.log_info(f"Removing {guest.custom_field_data['technology']} '{guest.name}' (vmid={guest.custom_field_data['vmid']})")
            guest.delete()
            self.log_success(f"Deleted vmid {guest.custom_field_data['vmid']} successfully")