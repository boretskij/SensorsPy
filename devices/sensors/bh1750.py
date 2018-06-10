import smbus2 as smbus

class bh1750:

    def __init__(self,bus=0,address=0x23):
        self.bus = smbus.SMBus(bus)
        self.address = address

    def get_data(self,type="lux"):
        source = self.__read()
        temp = source[0]

        source[0] = source[1]
        source[1] = temp

        lux = (int.from_bytes(source, byteorder='little')/1.2)
        return {"lux":lux}

    def __read(self):
        ## By default, set HIGH RESOLUTION MODE 1
        data = self.bus.read_i2c_block_data(self.address,0x20,2)
        return data

