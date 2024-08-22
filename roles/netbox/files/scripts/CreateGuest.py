from extras.scripts import *
from django.utils.text import slugify

from dcim.choices import VirtualDeviceContextStatusChoices
from dcim.models import DeviceRole, DeviceType, Site, Platform
from extras.models import CustomField
from virtualization.models import Cluster, VirtualMachine, VMInterface
from virtualization.choices import VirtualMachineStatusChoices
from ipam.models import IPAddress
from ipam.choices import IPAddressStatusChoices, IPAddressRoleChoices
from tenancy.models import Tenant, TenantGroup


class CreateGuest(Script):

    class Meta:
        name = "Create Guest"
        description = "Create a VM or LXC Guest system"
        scheduling_enabled=False

    guest_name = StringVar(
        description="Name of the guest",
        required=True
    )
    guest_role = ObjectVar(
        description="Ansible role of the guest",
        required=True,
        model=DeviceRole,
        default=DeviceRole.objects.get(name='debian')
    )
    guest_technology = ChoiceVar(
        description="LXC or VM",
        required=True,
        choices=[choice for choice in CustomField.objects.get_for_model(VirtualMachine).get(name='technology').choices],
        default=CustomField.objects.get_for_model(VirtualMachine).get(name='technology').default
    )
    guest_pool = ChoiceVar(
        description="Proxmox Pool of the guest",
        required=True,
        choices=[choice for choice in CustomField.objects.get_for_model(VirtualMachine).get(name='pool').choices],
        default=CustomField.objects.get_for_model(VirtualMachine).get(name='pool').default
    )
    guest_status = ChoiceVar(
        description="Status of the guest",
        required=True,
        choices=[(choice[0],choice[1]) for choice in VirtualMachineStatusChoices.CHOICES],
        default=VirtualMachineStatusChoices.STATUS_ACTIVE,
    )
    guest_site = ObjectVar(
        description="Site of the guest",
        required=True,
        model=Site,
        default=Site.objects.get(name='de-home')
    )
    guest_cluster = ObjectVar(
        description="Proxmox Cluster of the guest",
        required=True,
        model=Cluster,
        # default=Cluser.objects.get(name='PVE HOME')
        # default cannot be set since Cluster.objects is not defined?!
    )
    guest_platform = ObjectVar(
        description="Platform of the guest",
        required=True,
        model=Platform,
        #default=Platform.objects.get(slug='debian-11-standard-lxc')
    )
    guest_cpu = IntegerVar(
        description="CPU (nr. cores) of the guest",
        required=True,
        default=1
    )
    guest_mem = IntegerVar(
        description="Memory (GB) of the guest",
        required=True,
        default=1
    )
    guest_disk = IntegerVar(
        description="Disk (GB) of the guest",
        required=True,
        default=2
    )
    guest_existing_vmid = IntegerVar(
        description="VMID, if registering existing VM, number < 100 lets the script take the next free one",
        required=True,
        default=1
    )
#    guest_tenant = ObjectVar(
#        description="Tenant of the VM",
    #    required=True,
#        model=Tenant,
    #    default=Tenant.objects.get(name='Me')
#    )
    auto_deploy = BooleanVar(
        description="Sets 'Auto Deploy' and automatically deploys the guest",
        required=True,
        default=True
    )


    def run(self, data, commit):
        self.print_all(data)
        self.log_info(f"commit={commit}")

        vmid = data['guest_existing_vmid'] if data['guest_existing_vmid'] >= 100 else self.get_free_vmid()
        self.log_info(f"vmid={vmid}")


        # create virtual machine
        guest = VirtualMachine(
            name=data['guest_name'],
            role=data['guest_role'],
            site=data['guest_site'],
            cluster=data['guest_cluster'],
            platform=data['guest_platform'],
            status=data['guest_status'],
            vcpus=data['guest_cpu'],
            memory=data['guest_mem']*1024,
            disk=data['guest_disk'],
#            tenant=data['guest_tenant'],
            custom_field_data={
                'pool': data['guest_pool'],
                'technology': data['guest_technology'],
                'vmid': vmid,
                'auto_deploy': data['auto_deploy']
            }
        )
        self.log_info(f"saving VirtualMachine...")
        guest.save()
        self.log_success(f"done :-)")

        # create network interface
        interface = VMInterface(
            virtual_machine=guest,
            name="eth0",  # Modify this with the desired interface name
            description="Network interface for the guest",
            # Add any additional fields for the network interface here
        )
        self.log_info(f"saving VMInterface...")
        interface.save()
        self.log_success(f"done :-)")

        # create ip address
        ip_address = self.change_or_create_ip(
            address=f"192.168.2.{vmid}/24",
            dns_name="", # left empty for custom dns names
            assigned_object=interface,
#            tenant=data['guest_tenant'],
        )
        self.log_info(f"saving IPAddress {ip_address.address}...")
        ip_address.save()
        self.log_success(f"done :-)")

        guest.primary_ip4 = ip_address
        self.log_info(f"storing IPAddress as the guests primary IP...")
        guest.save()
        self.log_success(f"done :-)")

        pass

    def change_or_create_ip(self, address, dns_name, assigned_object, tenant=None):
        vrf = None
        status_value = IPAddressStatusChoices.STATUS_ACTIVE
        role_value = IPAddressRoleChoices.ROLE_SECONDARY
        nat_inside_value = None  # Replace with the actual IPAddress object if applicable
        
        ip_address = IPAddress(
            address=address,
            vrf=vrf,
#            tenant=tenant,
            status=status_value,
            role=role_value,
            assigned_object=assigned_object,
            nat_inside=nat_inside_value,
            dns_name=dns_name
        )
        print(f"IP address '{address}' created successfully.")

        return ip_address

    def print_all(self, data):
        self.log_info(f"guest_name : {data['guest_name']}")
        self.log_info(f"guest_role : {data['guest_role']}")
        self.log_info(f"guest_technology : {data['guest_technology']}")
        self.log_info(f"guest_pool : {data['guest_pool']}")
        self.log_info(f"guest_status : {data['guest_status']}")
        self.log_info(f"auto_deploy : {data['auto_deploy']}")