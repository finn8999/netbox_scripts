from utilities.exceptions import AbortScript
from dcim.choices import DeviceStatusChoices, DeviceFaceChoices
from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site, Location, Rack, Interface
from ipam.models import IPAddress
from virtualization.models import VirtualMachine, VMInterface
from extras.scripts import *

class createInterfaces(Script):

    class Meta:
        name = "Interfaces erstellen"
    
    def run(self, data, commit):
        allDevices = Device.objects.filter(interfaces=None)
        for device in allDevices:
            newInterface = Interface(
                device=device,
                name='Ethernet',
                type='1000base-t'
            )
            newInterface.full_clean()
            newInterface.save()
            self.log_info('Interface erstellt für Gerät: ' + str(device))
        self.log_success('Interfaces für ' + str(len(allDevices)) + ' Geräte erstellt')

        allVMs = VirtualMachine.objects.filter(interfaces=None)
        for VM in allVMs:
            newVMInterface = VMInterface(
                virtual_machine=VM,
                name='vEthernet'
            )
            newVMInterface.full_clean()
            newVMInterface.save()
            self.log_info('Interface erstellt für VM: ' + str(VM))
        self.log_success('Interfaces für ' + str(len(allVMs)) + ' VMs erstellt')

class validateNaming(Script):

    class Meta:
        name = "Überprüfe Namenskonvention"
    
    def run(self, data, commit):
        devices = Device.objects.all()
        for device in devices:
            if device.name != None:
                prefix = str(device.role.description) + '-' + str(device.site.facility)
                if not str(device.name).startswith(prefix):
                    self.log_warning(str(device.name) + ' (' + str(device.asset_tag) + ') ist falsch. Sollte mit "' + prefix + '" anfangen')
        self.log_info('Geräte überprüft')

        vms = VirtualMachine.objects.all()
        for vm in vms:
            if not str(vm.name).startswith('SRV'):
                self.log_warning(str(vm.name) + ' ist falsch. Sollte mit "SRV" anfangen')
        self.log_info('VMs überprüft')

        self.log_success('Namenskoventionsprüfung abgeschlossen')

class registerZabbix(Script):

    class Meta:
        name = "Registriere Geräte bei Zabbix"
    
    def run(self, data, commit):
        vms = VirtualMachine.objects.all()
        for vm in vms:
            if vm.primary_ip4 is not None:
                self.log_info(str(vm) + ' | ' + str(vm.primary_ip4))
        self.log_info('Alle möglichen Clients bei Zabbix registriert.')
