import yaml
import datetime

import lib.loader as DClass
import system.smbus as SMBus
import system.cache as Cache

import system.redisCache as Redis

import devices.sensors.pms3003 as pms


cache = Cache.Cache()

file = open('data/sensors.yaml')
sensors_data = yaml.load(file.read())['sensors']

bus = SMBus.SMBus(1)
bus_result = bus.detect_all_devices()

all_devices = {}

sensor_path = "devices.sensors."

pms = pms.PMS3003({'terminal':'/dev/ttyS1','baudrate':9600,'timeout':2})

init = {"pms3003":pms}

for i in range(1):
    time = datetime.datetime.utcnow().timestamp()
    data = {"pms":pms.get_data()}

    for bus in bus_result:
        devices = bus_result[bus]
        for device in devices:
            sensors = sensors_data[device]
            for sensor in sensors:
                module = sensor_path+sensors[sensor]+"."+sensors[sensor]
                if sensors[sensor]!="si7021" and sensors[sensor]!="bmp280" and sensors[sensor]!="bmp085":
                    load_module = DClass.load(module)()
                    init[sensors[sensor]] = load_module

## Test
for i in range(100000):
    time = datetime.datetime.utcnow().timestamp()

    data = {}
    for device in init:
        data[device] = init[device].get_data()

    cache.set(time,data)
