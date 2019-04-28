import smbus2 as smbus

class SMBus:

    def __init__(self,count=4):
        self.count = count
        self.bus = []
        self.busError = []
        self.sensors = {}

    def detect_all_i2c(self):
        count = self.count

        if type(count) is int:
            bus_array = range(0, count)
        elif type(count) is list:
            bus_array = count

        for num in bus_array:
            try:
                bus = smbus.SMBus(num)
            except:
                self.busError.append(num)
            else:
                self.bus.append(num)

        return self.bus

    def detect_all_devices(self,whitelist=[]):
        if (len(self.bus)==0):
            self.detect_all_i2c()

        devices = range(128)

        if (len(whitelist)>0):
            devices = whitelist

        for bus_num in self.bus:
            if bus_num not in self.sensors:
                self.sensors[bus_num]=[]
            bus = smbus.SMBus(bus_num)
            for device in devices:
                try:
                    bus.read_byte(device)
                except:
                    pass
                else:
                    self.sensors[bus_num].append(hex(device))
        return self.sensors

if __name__ == "__main__":
   bus = SMBus()
   print(bus.detect_all_devices())
