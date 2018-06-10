import serial

class PMS3003:

    __bytes = 24
    __stop_byte = 66

    def __init__(self,config):
        self.serial = port = serial.Serial(config['terminal'], baudrate = config['baudrate'], timeout = config['timeout'])

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

    def __read(self):
        data = self.serial.read(self.__bytes)
        return data


## Sample
## pms = PMS3003({'terminal':'/dev/ttyS1','baudrate':9600,'timeout':2})
## data = pms.get_data()
## print(data)
