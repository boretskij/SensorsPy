import os
import yaml
import time
import datetime
import socket
import json
import gzip
import asyncio
import threading
import multiprocessing

import lib.loader as DClass
import lib.databases as Databases
import system.smbus as SMBus
import system.mqtt as MQTT
import system.host as HOST
#import system.cache as Cache

# Quick patch for debug
import ssl
ssl.match_hostname = lambda cert, hostname: True

class Handler:

    __cache = {}

    __config = {}

    __monitor = {'queue':0,'attempt':0}

    __db__config = {'batch':10}

    __queue_size = -1

    __threads = []

    __bus_count = 1
    __prefixes = {}
    __devices_files = {}

    __devices = {'i2c':{},'serial':{},'system':{}}

    __devices_types = {'sensors':'sensors','displays':'displays'}

    __hostname = ""

    __status = multiprocessing.Manager().dict()

    def __init__(self,config):
        self.__bus_count = config['bus']['count']
        self.__prefixes = config['prefixes']
        self.__devices_files = config['files']
        self.__device_info = config['devices']
        self.__hostname = socket.gethostname()
        self.__config = config['custom']
        self.queue = multiprocessing.Queue()
        self.dead_queue = multiprocessing.Queue()
        self.log_queue = multiprocessing.Queue()
        self.thread = multiprocessing.Process
        self.threads = []
        self.scan_system();
        self.scan_i2c();
        self.scan_serial();

    def scan_system(self):
        interface = 'system'
        system = self.__get_devices_info(interface)
        print(system)
        for type in system:
            devices = system[type]
            for address in devices:
                self.__devices[interface][address] = {'source':{},'module':{}}
                for device in devices[address]:
                    self.__devices[interface][address]['module'][device] = {'type':type,'action':{}}
                    config = {} #{'terminal':address,'baudrate':devices[address][device]['baudrate'],'timeout':devices[address][device]['timeout']}
                    self.__devices[interface][address]['module'][device]['action'] = self.__include_module(device,{'interface':interface},address,config)
                    status_name = "{}/{}/{}".format(interface,address,device)
                    self.update_status(status_name,'scanned')
                    self.__devices[interface][address]['module'][device]['status_name'] = status_name
                    #self.append_status('scan_sensors',{'name':device,'interface':interface,'bus':address})

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
                    status_name = "{}/{}/{}".format(interface,address,device)
                    self.__devices[interface][address]['module'][device]['status_name'] = status_name
                    self.update_status(status_name,'scanned')

    def scan_i2c(self):
        whitelist = []
        interface = 'i2c'
        source = self.__device_info['interface'][interface]
        status = {}
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
                    status_name = "{}/{}/{}".format(interface,bus,device_name)
                    self.__devices[interface][bus]['module'][module_name]['status_name'] = status_name
                    self.update_status(status_name,'scanned')

    def sender(self,config):
        safety_delay = config['influxdb']['safety']['successfully']
        safety_critical = config['influxdb']['safety']['failed']
        batch_size = config['influxdb']['batch']
        successfully = 0
        failed = 0
        while True:
           time.sleep(2)
           current_size = self.queue.qsize()
           self.update_status('queue_size',current_size)
           self.update_status('dead_queue_size',self.dead_queue.qsize())
           if current_size > batch_size:
               print(self.dead_queue.qsize())
               current_timestamp = int(datetime.datetime.now().timestamp())
               result = self.write_to_db(self.queue,"InfluxDB")
               if result == True:
                   successfully = successfully + 1
                   self.update_status('write_to_db',{"comment":"Successfully on {}. Elements: {}".format(self.get_date(),current_size),"timestamp":current_timestamp})
               else:
                   self.update_status('write_to_db',{"comment":"Failed on {}. Elements: {}".format(self.get_date(),current_size),"timestamp":current_timestamp})
                   failed = failed + 1
           if successfully >= safety_delay: # Temporary!!! Not good, should replace on another format (prepare database data on sender side)
               successfully = 0
               #self.dump_data(self.dead_queue)
               while not self.dead_queue.empty():
                   self.dead_queue.get()
           if failed >= safety_critical:
               failed = 0
               self.dump_data(self.dead_queue)

    def bot(self,source,type="text"):
        def ping():
            return 'pong'

        def network_info():
            info = self.network_interfaces_info()
            self.update_status('network_interfaces',info)
            return info

        def status():
            return self.__status.copy()

        def is_up():
            return "up"

        def sender_status():
            return ""

        response = {'status':'success','content':'','uuid':''}

        command = ""

        if type == "text":
            command = source
        elif type == "json":
            command = source['command']
            response['uuid'] = "" if 'uuid' not in source else source['uuid']


        commands = {
          'is_up': is_up,
          'status': status,
          'network_info': network_info,
          'sender_status': sender_status
        }

        if command in commands:
            response['content'] = commands[command]()
        else:
            response['status'] = 'error'
            response['content'] = 'not found'
        return json.dumps(response)
    #@asyncio.coroutine
    def mqtt_receive(self,publish,content):
        source = content['data'].decode()
        source_json = None
        response = ""
        try:
            source_json = json.loads(source)
        except:
            source_json = None
        if source_json is not None:
            response = self.bot(source_json,"json")
        else:
            response = self.bot(source)

        asyncio.ensure_future(publish('', response)) #json.dumps(self.__status.copy())))

    # Test function
    def mqtt_test(self,mqtt):
        while True:
            yield from mqtt.publish('/my/test/output','pong')
            yield from asyncio.sleep(2)

    def client(self,config,func):
        loop = asyncio.get_event_loop()
        connect = "{}://{}:{}@{}:{}".format(config['type'],config['username'],config['password'],config['host'],config['port'])
        subscribe = config['topic'] + 'input/'
        publish = config['topic'] + 'output/'
        mqtt = MQTT.MQTT({'host':connect,'default_publish':publish, 'client_id': self.__hostname}) #'mqtts://guest:guest@mqtt.meteostation.online:8883'})
        status = self.__status.copy()
        status['type'] = "started"
        info_command = json.dumps({'status':'success','content':status})
        loop.run_until_complete(mqtt.init())
        asyncio.ensure_future(mqtt.subscribe(subscribe,func))
        asyncio.ensure_future(mqtt.handler())
        asyncio.ensure_future(mqtt.monitor())
        asyncio.ensure_future(mqtt.publish('',info_command))
        loop.run_forever()

    def get_sensor_data(self, sensors,wait=2):
        while True:
            for sensor in sensors:
                source = sensor['action'].get_data()
                self.update_status(sensor['status_name'],{"comment":"Last get date: {}".format(str(datetime.datetime.now())),"timestamp":int(datetime.datetime.now().timestamp()),"data":source})
                self.queue.put({'data':source,
                                'sensor':sensor['name'],
                                'interface':sensor['interface'],
                                'bus':sensor['bus'],
                                'time':self.__prepare_influx_time(),
                                'hostname':self.__hostname})
#                print("Queue len: {}".format(self.queue.qsize()))
 #               print({'data':source,'name':sensor['name'],'interface':sensor['interface'],'bus':sensor['bus']})
            time.sleep(wait)

    def get_date(self):
        return str(datetime.datetime.now())

    def append_status(self,key,value):
        if key in self.__status:
            if type(self.__status[key]) is not list:
                self.__status[key] = [] #multiprocessing.Manager().list(range(10))
        else:
            self.__status[key] = [] #multiprocessing.Manager().list(range(10))
        self.__status[key].append(value)
        #print(list(self.__status[key]))

    def update_status(self,key,value):
        self.__status[key] = value

    def get_status_key(self,key):
        return self.__status[key]

    def get_status(self):
        return self.__status.copy()

    def network_interfaces_info(self):
        self.host = HOST.HostSystem()
        result = {}
        for type in self.__config['host']['interfaces']:
            interface = self.__config['host']['interfaces'][type]
            result[type] = {'interface':interface,'IPv4':self.host.get_ip_address(interface),'last_update':self.get_date()}
        return result

    def init(self):
        data = {}
        threads = []
        t = self.thread(target=self.sender,args=(self.__config['databases'],))
        t.start()
        print(self.__config['servers']['mqtt'])
        self.__config['servers']['mqtt']['topic'] = "/{}/{}/".format(self.__config['servers']['mqtt']['topic'],self.__hostname)
        t2 = self.thread(target=self.client,args=(self.__config['servers']['mqtt'],self.mqtt_receive,))
        t2.start()
        self.host = HOST.HostSystem()
        self.threads.append({'thread':t,'description':'Main'});
        self.threads.append({'thread':t2,'description':'MQTT Handler'});
        self.update_status('network_interfaces',self.network_interfaces_info())
        print(self.__status)
        for interface in self.__devices:
            for bus in self.__devices[interface]:
                sensors = []
                for module in self.__devices[interface][bus]['module']:
                    type = self.__devices[interface][bus]['module'][module]['type']
                    if type==self.__devices_types['sensors']:
                        sensors.append({'action':self.__devices[interface][bus]['module'][module]['action'],
                                        'name':module,
                                        'interface':interface,
                                        'bus':bus,
                                        'status_name':self.__devices[interface][bus]['module'][module]['status_name']})
                        #data[module] = self.__devices[interface][bus]['module'][module]['action'].get_data()
                        #data[module] = self.get_sensor_data(self.__devices[interface][bus]['module'][module]['action'])
                print(sensors)
                t = self.thread(target=self.get_sensor_data,args=(sensors,))
                t.start()
                self.threads.append({'thread':t,'description':"Sensor with interface {} on bus {}".format(interface,bus)});
                #self.__threads.append(t)
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

    def dump_data(self, queue):
        path = os.path.dirname(os.path.realpath(__file__))
        folder_name = datetime.datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d')
        full_path = "{}/data/{}/".format(path,folder_name)
        file_full_path = "{}/{}".format(full_path,"dump-{}.sp.gz".format(datetime.datetime.fromtimestamp(time.time()).strftime('%H-%M-%S')))
        try:
            os.makedirs(full_path)
        except:
            print("Failed create folder")
        data = ""
        while not queue.empty():
            element = queue.get()
            print(element)
            data = data + "{}\n".format(json.dumps(element))
        source = gzip.compress(data.encode(),compresslevel=9)
        file = open(file_full_path,'wb+')
        file.write(source)
        file.flush()
        file.close()


    def monitor(self, info):
        reboot_batch = self.__config['reboot']['batch']
        reboot_attempt = self.__config['reboot']['attempt']
        path = os.path.dirname(os.path.realpath(__file__))
        folder_name = datetime.datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d_%H_%M_%S')
        full_path = "{}/data/{}/".format(path,folder_name)
        if info['queue']>=reboot_batch or info['attempt']>=reboot_attempt:
            print("Initiate reboot...")
            os.makedirs(full_path)
            file_full_path = "{}/{}".format(full_path,"dump.sp")
            file = open(file_full_path,'w+')
            file.write(json.dumps(info['source']))
            file.flush()
            file.close()
            time.sleep(2)
            print("Dump finished. Start reboot...")
            os.system('shutdown -r now')
#{'interface': 'i2c', 'bus': 0, 'data': {'humidity': 37.6786759855756, 'temperature': 23.024540384137072, 'pressure': 100545.53208274403}, 'name': 'bme280'}
    def prepare_to_db(self,element,table,database_type="InfluxDB"):
        result = ""
        if database_type == "InfluxDB":
            template = "{},{} {} {}\n"
            tags = []
            values = []
            time = element['time']
            for key in element:
                if key == 'data':
                    for value in element[key]:
                        values.append("{}={}".format(value,element[key][value]))
                elif key != 'time':
                    tags.append("{}={}".format(key,element[key]))
            result = result + template.format(table,",".join(tags),",".join(values),time)
        return result

    def write_to_db(self,queue,database,namespace="measurements"):
        result = ""
        influx = Databases.InfluxDB(self.__config['databases']['influxdb'])
        current_size = queue.qsize()
        for i in range(0,current_size):
            data = self.queue.get()
            self.dead_queue.put(data)
            result = result + self.prepare_to_db(data,namespace)
        response = influx.write_to_db(result)
        return response['status']

#['__abstractmethods__', '__class__', '__del__', '__delattr__', '__dict__', '__dir__', '__doc__', '__enter__', '__eq__', '__exit__', '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__', '__init__', '__iter__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__next__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '_abc_cache', '_abc_negative_cache', '_abc_negative_cache_version', '_abc_registry', '_checkClosed', '_checkReadable', '_checkSeekable', '_checkWritable', '_check_close', '_close_conn', '_get_chunk_left', '_method', '_peek_chunked', '_read1_chunked', '_read_and_discard_trailer', '_read_next_chunk_size', '_read_status', '_readall_chunked', '_readinto_chunked', '_safe_read', '_safe_readinto', 'begin', 'chunk_left', 'chunked', 'close', 'closed', 'code', 'debuglevel', 'detach', 'fileno', 'flush', 'fp', 'getcode', 'getheader', 'getheaders', 'geturl', 'headers', 'info', 'isatty', 'isclosed', 'length', 'msg', 'peek', 'read', 'read1', 'readable', 'readinto', 'readinto1', 'readline', 'readlines', 'reason', 'seek', 'seekable', 'status', 'tell', 'truncate', 'url', 'version', 'will_close', 'writable', 'write', 'writelines']

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

    time.sleep(10)

    full_path = "{}/{}".format(os.path.dirname(os.path.realpath(__file__)),'config.yaml')
    configuration = yaml.load(open(full_path,'r').read());
    databases = configuration['databases']
    reboot = configuration['actions']['reboot']
    save = configuration['actions']['save']
    prefixes = configuration['prefixes']
    interfaces = configuration['interface']
    host = configuration['host']
    servers = configuration['servers']
#    time.sleep(180)
#    quit();
    handler = Handler(
                      {'custom':
                        {'databases':databases,'reboot':reboot,'save':save,'host':host,'servers':servers},
                      'bus':{'count':1},
                      'prefixes':prefixes,
                      'files':'dd', 'devices':{'interface':interfaces}})
    handler.init()
    while True:
#        data = handler.get_all_sensors_data()
        time.sleep(0.1)
#        print(data)
#        handler.write_to_db(data,"InfluxDB")
#        quit()
