import serial

class PMS3003:

    __bytes = 24
    __stop_byte = 66

    __config = {}

    def __init__(self,config):
        self.__config = config
        self.__open()

    def __decode(self,upper,lower):
        return ((upper << 8) + lower)

    def get_data(self):
        source = self.__read()

        pm01_cf = self.__decode(source[4],source[5])
        pm25_cf = self.__decode(source[6],source[7])
        pm100_cf = self.__decode(source[8],source[9])

        pm01 = self.__decode(source[10],source[11])
        pm25 = self.__decode(source[12],source[13])
        pm100 = self.__decode(source[14],source[15])

        data = {
               'pm01_cf': pm01_cf,
               'pm25_cf': pm25_cf,
               'pm100_cf': pm100_cf,
               'pm01': pm01,
               'pm25': pm25,
               'pm100': pm100
               }

        return data

    def __open(self):
        self.serial = serial.Serial(self.__config['terminal'], baudrate = self.__config['baudrate'], timeout = self.__config['timeout'])

    def __read(self):
        data = self.serial.read(self.__bytes)
        sum = 0
        for i in range(0,21):
            sum += data[i]

        checksum = self.__decode(data[22],data[23])

        if (sum!=checksum):
            self.serial.close()
            self.__open()
            return self.__read()

        return data


## Sample
#while True:
#    pms = PMS3003({'terminal':'/dev/ttyS1','baudrate':9600,'timeout':2})
#    data = pms.get_data()
#    print(data)
