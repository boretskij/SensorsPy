import smbus2 as smbus

class SMBus:

    def __init__(self,count=4):
        self.count = count
        self.bus = []
        self.busError = []
        self.sensors = {}
    
    def detect_all_i2c(self):
        for num in range(0,self.count):
            try:
                bus = smbus.SMBus(num)
            except:
                self.busError.append(num)
            else:
                self.bus.append(num)
        return self.bus
    
    def detect_all_devices(self):
        if (len(self.bus)==0):
            self.detect_all_i2c()
        
        for bus_num in self.bus:
            self.sensors = {bus_num:[]}
            bus = smbus.SMBus(bus_num)
            for device in range(128):
                try:
                    bus.read_byte(device)
                except:
                    pass
                else:
                    self.sensors[bus_num].append(hex(device))
        return self.sensors

bus = SMBus()
print(bus.detect_all_devices())

'''
try:
    bus = smbus.SMBus(0)
except:
    print("Not found")

for device in range(128):
    try:
        bus.read_byte(device)
        print(hex(device))
    except:
        t = "d"
'''
