import yaml
import time
import datetime
import socket

import lib.loader as DClass
import system.smbus as SMBus
import lib.databases as Databases
#import system.cache as Cache


class Handler:

    __cache = {}

    __config = {}

    __db__config = {'batch':10}

    __bus_count = 1
    __prefixes = {}
    __devices_files = {}

    __devices = {'i2c':{},'serial':{}}
    __device_info_path = ""

    __devices_types = {'sensors':'sensors','displays':'displays'}

    __hostname = ""

    def __init__(self,config):
        self.__bus_count = config['bus']['count']
        self.__prefixes = config['prefixes']
        self.__devices_files = config['files']
        self.__device_info_path = config['devices']['path']
        self.__device_info = self.__load_yaml(self.__device_info_path)
	self.__hostname = socket.gethostname()
        self.__config = config['custom']
        self.scan_i2c();
        self.scan_serial();

    def scan_serial(self):
        interface = 'serial'
        serial = self.__get_devices_info(interface);
        for type in serial:
            devices = serial[type]
            for address in devices:
                self.__devices[interface][address] = {'source':{},'module':{}}
                for device in devices[address]:
                    self.__devices[interface][address]['module'][device] = {'type':type,'action':{}}
                    config = {'terminal':address,'baudrate':devices[address][device]['baudrate'],'timeout':devices[address][device]['timeout']}
                    self.__devices[interface][address]['module'][device]['action'] = self.__include_module(device,{'interface':interface},address,config)

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
                    self.__devices[interface][bus]['module'][module_name]['action'] = self.__include_module(module_name,{'interface':interface,'number':bus},device)

    def get_all_sensors_data(self):
        data = {}
        for interface in self.__devices:
            for bus in self.__devices[interface]:
                for module in self.__devices[interface][bus]['module']:
                    type = self.__devices[interface][bus]['module'][module]['type']
                    if type==self.__devices_types['sensors']:
                        data[module] = self.__devices[interface][bus]['module'][module]['action'].get_data()
        return data

    def show_data_displays(self,data={}):
        for interface in self.__devices:
            for bus in self.__devices[interface]:
                for module in self.__devices[interface][bus]['module']:
                    type = self.__devices[interface][bus]['module'][module]['type']
                    if type==self.__devices_types['displays']:
                        for line_number in data['text']:
                            full_text = data['text'][line_number]
                            self.__devices[interface][bus]['module'][module]['action'].setCursor(0,line_number)
                            self.__devices[interface][bus]['module'][module]['action'].printstr(full_text)
                            if 'backlight' in data:
                                if data['backlight']==True:
                                    self.__devices[interface][bus]['module'][module]['action'].backlight()
                                elif data['backlight']==False:
                                    self.__devices[interface][bus]['module'][module]['action'].noBacklight()

    def __load_yaml(self,path):
        file = open(path,'r')
        return yaml.load(file.read())

    def write_to_db(self,data,database):
        if database=="InfluxDB":
            time = self.__prepare_influx_time()
            source_data = ""
            template = '{},sensor={},hostname={} value={} {}\n'
            for device in data:
                for measurement in data[device]:
                    source_data += template.format(measurement,device,self.__hostname,data[device][measurement],time)
            cache_value = self.__cache_get("influxdb/batchCount")
            if cache_value==None:
                self.__cache_set("influxdb/batchCount",1)
                self.__cache_set("influxdb/batchData",source_data)
            elif cache_value<self.__db__config['batch']:
                batch_value = self.__cache_get("influxdb/batchData")+source_data
                self.__cache_set("influxdb/batchData",batch_value)
                current = cache_value+1
                self.__cache_set("influxdb/batchCount",current)
            elif cache_value>=self.__db__config['batch']:
                data = self.__cache_get("influxdb/batchData")+source_data
                influx = Databases.InfluxDB(self.__config['databases']['influx'])
                result = influx.write_to_db(data)
		if result is not None:
                    self.__cache_set("influxdb/batchCount",0)
                    self.__cache_set("influxdb/batchData","")
            print(source_data)
            source_data = ""

    def __get_device_name(self,interface,address):
        device = {}
        info_devices = self.__get_devices_info(interface)
        for type in info_devices:
            for device_addr in info_devices[type]:
                if str(address)==str(device_addr):
                    device = {'name':info_devices[type][device_addr],'type':type}
        return device

    def __prepare_influx_time(self):
        time = str(datetime.datetime.utcnow().timestamp()*1000000).replace(".0","")+"000"
        return time

    def __cache_set(self,key,value):
        self.__cache[key] = value

    def __cache_get(self,key):
        cache_value = None

        if key in self.__cache:
            cache_value = self.__cache[key]

        return cache_value

    def __get_devices_info(self,interface):
        if interface in self.__device_info['interface']:        
            return self.__device_info['interface'][interface]
        else:
            return {}
    def __include_module(self,device,bus,address,additional={}):
        module = None
        module_status = False
        for prefix in self.__prefixes:
            module_path = self.__prefixes[prefix] + device + "." + device.upper()
            try:
                if bus['interface']=='i2c':
                    module = DClass.load(module_path)(bus['number'],int(address,16))
                elif bus['interface']=='serial':
                    module = DClass.load(module_path)(additional)
                module_status = True
            except:
                module_status = False
                module = None
            if module_status:
                break
        return module


if __name__ == "__main__":
    ## Just sample
    handler = Handler(
                      {'custom':{'databases':{'influx':
                                {'host':'','port':443,'ssl':True,'database':'user','username':'user','password':'password'}}},
                      'bus':{'count':1},
				       'prefixes':{'sensors':'devices.sensors.'},
                                       'files':'dd', 'devices':{'path':'data/devices.yaml'}})
    while True:
        data = handler.get_all_sensors_data()
        time.sleep(1)
#        print(data)
        handler.write_to_db(data,"InfluxDB")
