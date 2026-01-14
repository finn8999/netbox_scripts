from utilities.exceptions import AbortScript
from dcim.choices import DeviceStatusChoices, DeviceFaceChoices
from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site, Location, Rack, Interface
from ipam.models import IPAddress
from virtualization.models import VirtualMachine, VMInterface
from extras.scripts import *


class AddDevice(Script):

    class Meta:
        name = "Gerät inventarisieren"
        fieldsets = (
            ('Gerät', ('gerätename', 'geräterolle', 'status', 'beschreibung')),
            ('Hardware', ('hersteller', 'gerätetyp', 'seriennummer', 'inventarnummer')),
            ('Lokation', ('standort', 'lokation')),
            ('Rack (nur wenn bereits im Rack eingebaut)', ('rack', 'rackseite', 'höheneinheit')),
        )
        scheduling_enabled = False

    # Asset Tag List, sorted by highest
    allDevices = Device.objects.all()
    assetTagList = []
    for device in allDevices:
        assetTagList.append(device.asset_tag)
    assetTagList.sort(key=lambda v: (v is None, -(int(v)) if v is not None else 0))
    
    # Formularfelder
    gerätename = StringVar(required=False)
    geräterolle = ObjectVar(model=DeviceRole, required=True)
    status = ChoiceVar(choices=DeviceStatusChoices, required=True, default='active')
    beschreibung = StringVar(required=False)

    hersteller = ObjectVar(model=Manufacturer, required=True)
    gerätetyp = ObjectVar(model=DeviceType, required=True, query_params={'manufacturer_id': '$hersteller'})
    seriennummer = StringVar(required=False, description='vom Hersteller vergebene Seriennummer')
    inventarnummer = IntegerVar(label='Inventar-Nr.', description='Intern vergebene, einzigartige Inventarnummer (Aufkleber)',required=True, min_value=int(assetTagList[0])+1, max_value=int(assetTagList[0])+1, default=int(assetTagList[0])+1)

    standort = ObjectVar(model=Site, required=True, default=2)
    lokation = ObjectVar(model=Location, required=False, query_params={'site_id': '$standort'}, default=37)

    rack = ObjectVar(model=Rack, required=False, query_params={'location_id': '$lokation'})
    rackseite = ChoiceVar(choices=DeviceFaceChoices, required=False)
    höheneinheit = IntegerVar(label='Höheneinheit (HE)', description='Niedrigste HE, die vom Gerät belegt wird', required=False)

    # Ausführung des Scripts
    def run(self, data, commit):
        if str(data['rackseite']) != '' and str(data['rack']) == 'None':
            self.log_warning('Wenn eine Rackseite gesetzt ist, muss auch ein Rack definiert werden')
            raise AbortScript('Rack nicht definiert:' + str(data['rackseite']))

        if str(data['höheneinheit']) != 'None':
            if str(data['rack']) == 'None' or str(data['rackseite']) == 'None':
                self.log_warning('Wenn die HE gesetzt ist, muss auch ein Rack und eine Rackseite definiert werden')
                raise AbortScript('Rack oder Rackseite ist leer')
            chosenRack = Rack.objects.get(name=data['rack'], site=data['standort'], location=data['lokation'])
            chosenDeviceType = DeviceType.objects.get(model=data['gerätetyp'])
            availableUnits = list(dict.fromkeys([int(d) for d in chosenRack.get_available_units(u_height=chosenDeviceType.u_height, rack_face=None, exclude=None)]))
            if data['höheneinheit'] not in availableUnits:
                self.log_warning('HE' + str(data['höheneinheit']) + ' ist im Rack bereits belegt. Freie HEs: ' + str(availableUnits))
                raise AbortScript('HE ist bereits belegt')

        newDevice = Device(
                name=data['gerätename'],
                role=data['geräterolle'],
                description=data['beschreibung'],
                device_type=data['gerätetyp'],
                serial=data['seriennummer'],
                asset_tag=data['inventarnummer'],
                site=data['standort'],
                location=data['lokation'],
                rack=data['rack'],
                face=data['rackseite'],
                position=data['höheneinheit'],
                status=data['status'],
        )
        newDevice.full_clean()
        newDevice.save()
        self.log_info('Gerät erstellt')

        newInterface = Interface(
            device=newDevice,
            name='Ethernet',
            type='1000base-t'
        )
        newInterface.full_clean()
        newInterface.save()
        self.log_info('Interface für Gerät erstellt')

        self.log_success(f'Gerät inventarisiert: {newDevice}')