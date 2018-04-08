import yaml
import smbus2 as smbus

import system.smbus as SMBus
import devices.sensors.sht21

bus = SMBus.SMBus()
print(bus.detect_all_devices())

## Test
#bus = smbus.SMBus(1)

#with devices.sensors.sht21.SHT21(bus) as sht21:
#     print ("Temperature: %s"%sht21.read_temperature())
#     print ("Humidity: %s"%sht21.read_humidity())

