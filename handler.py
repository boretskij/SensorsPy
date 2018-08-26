import yaml
import datetime

import lib.loader as DClass
import system.smbus as SMBus
#import system.cache as Cache


class Handler:

    __bus_count = 1
    __prefixes = {}
    __devices_files = {}

    __devices = {'i2c':{}}
    __device_info_path = ""
	
	
    def __init__(self,config):
        self.__bus_count = config['bus']['count']
        self.__prefixes = config['prefixes']
        self.__devices_files = config['files']
        self.__device_info_path = config['devices']['path']
        self.__device_info = self.__load_yaml(self.__device_info_path)
        self.scan_i2c();
	
    def scan_i2c(self):
        bus = SMBus.SMBus(self.__bus_count)
        bus_devices = bus.detect_all_devices()
        interface = 'i2c'
        for bus in bus_devices:
            self.__devices[interface][bus] = {'source':{},'module':{}}
            self.__devices[interface][bus]['source'] = bus_devices[bus]
            for device in self.__devices[interface][bus]['source']:
                device_description = self.__get_device_name(interface,device)
                device_type = device_description['type']
                for device_name in device_description['name']:
                    module_name = device_description['name'][device_name]
                    self.__devices[interface][bus]['module'][module_name] = {'type':device_type,'action':{}}
                    self.__devices[interface][bus]['module'][module_name]['action'] = self.__include_module(module_name,bus,device)

    def __load_yaml(self,path):
        file = open(path,'r')
        return yaml.load(file.read())

    def __get_device_name(self,interface,address):
        device = {}
        info_devices = self.__get_devices_info(interface)
        for type in info_devices:
            for device_addr in info_devices[type]:
                if str(address)==str(device_addr):
                    device = {'name':info_devices[type][device_addr],'type':type}
        return device

    def __get_devices_info(self,interface):
        return self.__device_info['interface'][interface]

    def __include_module(self,device,bus,address):
        module = None
        module_status = False
        for prefix in self.__prefixes:
            module_path = self.__prefixes[prefix] + device + "." + device.upper()
            try:
                module = DClass.load(module_path)(bus,int(address,16))
                module_status = True
            except:
                module_status = False
                module = None
            if module_status:
                break
        return module


if __name__ == "__main__":
    ## Just sample
    handler = Handler({'bus':{'count':2},
				       'prefixes':{'sensors':'devices.sensors.','displays':'devices.displays.'},'files':'dd', 'devices':{'path':'data/devices.yaml'}})