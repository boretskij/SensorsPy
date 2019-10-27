import serial

class PMS5003ST:

    __bytes = 38
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

        n03 = self.__decode(source[16],source[17])
        n05 = self.__decode(source[18],source[19])
        n10 = self.__decode(source[20],source[21])
        n25 = self.__decode(source[22],source[23])
        n50 = self.__decode(source[24],source[25])
        n100 = self.__decode(source[26],source[27])

        hcho = self.__decode(source[28],source[29]) / 1000.0
        temperature = self.__decode(source[30],source[31]) / 10.0
        humidity = self.__decode(source[32],source[33]) / 10.0
        data = {
               'pm01_cf': pm01_cf,
               'pm25_cf': pm25_cf,
               'pm100_cf': pm100_cf,
               'pm01': pm01,
               'pm25': pm25,
               'pm100': pm100,
               "n03": n03,
               "n05": n05,
               "n10": n10,
               "n25": n25,
               "n50": n50,
               "n100": n100,
               "hcho": hcho,
               "temperature": temperature,
               "humidity": humidity
               }

        return data

    def __open(self):
        self.serial = serial.Serial(self.__config['terminal'], baudrate = self.__config['baudrate'], timeout = self.__config['timeout'])

    def __read(self):
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()
        data = self.serial.read(self.__bytes)
        sum = 0
        for i in range(0,37):
            sum += data[i]

        checksum = self.__decode(data[38],data[39])

        if (sum!=checksum):
            self.serial.close()
            self.__open()
            return self.__read()

        return data


## Sample
#while True:
#    pms = PMS5003ST({'terminal':'/dev/ttyS2','baudrate':9600,'timeout':2})
#    data = pms.get_data()
#    print(data)
