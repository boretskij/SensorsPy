import serial

class ZE08:

    __bytes = 9
    __stop_byte = 66

    __config = {}

    def __init__(self,config):
        self.__config = config
        self.__open()

    def __decode(self,upper,lower):
        return ((upper << 8) + lower)

    def get_data(self):
        source = self.__read()


        fm = self.__decode(source[4],source[5])
        fm = fm / 1000
        
        data = {
               'fm': fm
               }

        return data

    def __open(self):
        self.serial = serial.Serial(self.__config['terminal'], baudrate = self.__config['baudrate'], timeout = self.__config['timeout'])

    def __read(self):
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()
        data = self.serial.read(self.__bytes)
        sum = 0
        for i in range(1,8):
            sum += data[i]

        checksum = 256 - data[8]

        #print("{}/{}".format(sum,checksum))
        #quit()

        if (sum!=checksum):
            self.serial.close()
            self.__open()
            return self.__read()

        return data


## Sample
# import time
# while True:
#    pms = ZE08({'terminal':'/dev/ttyS1','baudrate':9600,'timeout':2})
#    data = pms.get_data()
#    time.sleep(2)
#    print(data)
