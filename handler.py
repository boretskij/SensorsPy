import os
import yaml
import time
import datetime
import socket
import json

import lib.loader as DClass
import system.smbus as SMBus
import lib.databases as Databases
#import system.cache as Cache


class Handler:

    __cache = {}

    __config = {}

    __monitor = {'queue':0,'attempt':0}

    __db__config = {'batch':10}

    __bus_count = 1
    __prefixes = {}
    __devices_files = {}

    __devices = {'i2c':{},'serial':{},'system':{}}

    __devices_types = {'sensors':'sensors','displays':'displays'}

    __hostname = ""

    def __init__(self,config):
        self.__bus_count = config['bus']['count']
        self.__prefixes = config['prefixes']
        self.__devices_files = config['files']
        self.__device_info = config['devices']
        self.__hostname = socket.gethostname()
        self.__config = config['custom']
        self.scan_system();
        self.scan_i2c();
        self.scan_serial();

    def scan_system(self):
        interface = 'system'
        system = self.__get_devices_info(interface)
        for type in system:
            devices = system[type]
            for address in devices:
                self.__devices[interface][address] = {'source':{},'module':{}}
                for device in devices[address]:
                    self.__devices[interface][address]['module'][device] = {'type':type,'action':{}}
                    config = {} #{'terminal':address,'baudrate':devices[address][device]['baudrate'],'timeout':devices[address][device]['timeout']}
                    self.__devices[interface][address]['module'][device]['action'] = self.__include_module(device,{'interface':interface},address,config)

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
        whitelist = []
        interface = 'i2c'
        source = self.__device_info['interface'][interface]
        for type in source:
            for address in source[type]:
                whitelist.append(int(address,0))
        bus = SMBus.SMBus(self.__bus_count)
        bus_devices = bus.detect_all_devices(whitelist)
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

    def monitor(self, info):
        reboot_batch = self.__config['reboot']['batch']
        reboot_attempt = self.__config['reboot']['attempt']
        path = os.path.dirname(os.path.realpath(__file__))
        folder_name = datetime.datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d_%H_%M_%S')
        full_path = "{}/data/{}/".format(path,folder_name)
        if info['queue']>=reboot_batch or info['attempt']>=reboot_attempt:
            print("Initiate reboot...")
            os.mkdir(full_path)
            file_full_path = "{}/{}".format(full_path,"dump.sp")
            file = open(file_full_path,'w+')
            file.write(json.dumps(info['source']))
            file.flush()
            file.close()
            time.sleep(2)
            print("Dump finished. Start reboot...")
            os.system('shutdown -r now')

    def write_to_db(self,data,database,namespace="measurements"):
        if database=="InfluxDB":
            time = self.__prepare_influx_time()
            source_data = ""
            template = '{},sensor={},hostname={} {} {}\n'
            for device in data:
                values = []
                for measurement in data[device]:
                    values.append("{}={}".format(measurement,data[device][measurement]))
                source_data += template.format(namespace,device,self.__hostname,",".join(values),time)
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
                influx = Databases.InfluxDB(self.__config['databases']['influxdb'])
                result = influx.write_to_db(data)
                if result is not None:
                    self.__cache_set("influxdb/batchCount",0)
                    self.__cache_set("influxdb/batchData","")
                else:
                    batch_value = self.__cache_get("influxdb/batchData")+source_data
                    self.__cache_set("influxdb/batchData",batch_value)
                    current = cache_value+1
                    self.__cache_set("influxdb/batchCount",current)
                    self.__monitor['attempt'] = self.__monitor['attempt'] + 1
                    self.__monitor['queue'] = self.__cache_get("influxdb/batchCount")
                    self.monitor({'queue':self.__monitor['queue'],
                                  'attempt':self.__monitor['attempt'],
                                  'source':{
                                            'data':self.__cache_get("influxdb/batchData"),
                                            'count': self.__cache_get("influxdb/batchCount")
                                 }})
#                    if cache_value>=self.__config['save']['batch']:
#                        self.save_data(batch_value)
            print(source_data)
            source_data = ""

    def save_data(self,data,name,path="data"):
        fullPath = "{}/{}".format(path,name)
        f = open(fullPath,'w+')
        f.write(data)
        f.close()

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
                print(module_path)
                if bus['interface']=='i2c':
                    module = DClass.load(module_path)(bus['number'],int(address,16))
                elif bus['interface']=='serial':
                    module = DClass.load(module_path)(additional)
                elif bus['interface']=='system':
                    module = DClass.load(module_path)()
                module_status = True
            except:
                module_status = False
                module = None
            if module_status:
                break
        return module


if __name__ == "__main__":
    ## Just sample
    full_path = "{}/{}".format(os.path.dirname(os.path.realpath(__file__)),'config.yaml')
    configuration = yaml.load(open(full_path,'r').read());
    databases = configuration['databases']
    reboot = configuration['actions']['reboot']
    save = configuration['actions']['save']
    prefixes = configuration['prefixes']
    interfaces = configuration['interface']
#    quit();
    handler = Handler(
                      {'custom':{'databases':databases,'reboot':reboot,'save':save},
                      'bus':{'count':1},
                      'prefixes':prefixes,
                      'files':'dd', 'devices':{'interface':interfaces}})
    while True:
        data = handler.get_all_sensors_data()
        time.sleep(1)
#        print(data)
        handler.write_to_db(data,"InfluxDB")
#        quit()
