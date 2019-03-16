import serial

class SDS011:

    __bytes = 10
    # __stop_byte = 66

    __config = {}

    def __init__(self,config):
        self.__config = config
        self.__open()

    def __decode(self,upper,lower):
        return ((upper << 8) + lower)

    def get_data(self):
        source = self.__read()

        pm25 = (self.__decode(source[3],source[2])/10)
        pm100 = (self.__decode(source[5],source[4])/10)
        data = {'pm25':pm25,'pm100':pm100}

        return data

    def __open(self):
        self.serial = serial.Serial(self.__config['terminal'], baudrate = self.__config['baudrate'], stopbits=1, parity="N",timeout = self.__config['timeout'])

    def __read(self):
        data = self.serial.read(self.__bytes)

        sum = 0
        for i in range(2,8):
            sum += data[i]
        sum = sum - 256
        checksum = data[8]

        if (sum!=checksum):
            self.serial.close()
            self.__open()
            return self.__read()

        return data


## Sample
#while True:
#    sds = SDS011({'terminal':'/dev/ttyS1','baudrate':9600,'timeout':2})
#    data = sds.get_data()
#    print(data)
#    quit()
