'''
* THIS IS A BETA VERSION FOR MHZ19B *
* PLEASE CHECK *

Information about corrections for values from: https://mysku.ru/blog/aliexpress/59397.html
Measurements settings: https://revspace.nl/MHZ19
'''
import serial

class MHZ19B:

    __bytes = 9

    __config = {}

    __data = {'5000ppm':bytearray([0xFF, 0x01, 0x99, 0x00, 0x00, 0x00, 0x13, 0x88, 0xCB]),
              'read': bytearray([0xFF, 0x01, 0x86, 0x00, 0x00, 0x00, 0x00, 0x00, 0x79])}

    def __init__(self,config):
        self.__config = config
        self.__open()
        self.__set()

    def __decode(self,high,low):
        return ((high << 8) + low)

    def __open(self):
        self.serial = serial.Serial(self.__config['terminal'], baudrate = self.__config['baudrate'], timeout = self.__config['timeout'])

    def __checksum(self,data):
        sum = 0
        status = True
        for i in range(1,8):
            sum += data[i]
        sum = ((255-sum)+1)
        print(sum,data[8])
        if (sum!=data[8]):
            status = False

        return status

    def __set(self):
        self.serial.write(self.__data['5000ppm'])
        data = self.serial.read(self.__bytes)
        return self.__checksum(data)

    def __read(self):
        self.serial.write(self.__data['read'])
        data = self.serial.read(self.__bytes)
        return data

    def get_data(self):
        source = self.__read()
        value = self.__decode(source[2],source[3])
        value = value * 0.4
        return value
## Sample
mh = MHZ19B({'terminal':'/dev/ttyS1','baudrate':9600,'timeout':2})
while True:
    data = mh.get_data()
    print(data)

