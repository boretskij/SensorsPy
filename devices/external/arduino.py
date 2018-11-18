'''
This is an experimental variant for connection with Arduino. 
Created within 10 minutes, horrible = ) 
Will be rewritten with normal (not experimental) protocol and hardware implementation not using USB

I strongly not recommend this way for Arduino connection.
Use hardware serial on Arduino and on your single board computer.

'''

import serial
import time

class ARDUINO:

    __bytes = 12

    def __init__(self,config):
        self.__config = config
        self.__adcvoltage = config['adc']['voltage']
        self.__adcbit = config['adc']['bit']
        self.__adcnum = (self.__adcvoltage)/(1 << self.__adcbit)
        self.__open()
        print(self.__adcnum)

    def __open(self):
        self.serial = serial.Serial(self.__config['terminal'], baudrate = self.__config['baudrate'], timeout = self.__config['timeout'])
        self.serial.setDTR(False)
        time.sleep(2)
        self.__write('helo')
        time.sleep(1)
        self.__read()

    def __read(self):
        data = self.serial.read(self.__bytes)
        sum = 0
        checksum_status = False
        for i in range(0,6):
            sum = sum + data[i]
        checksum = data[6]*127+data[7]
        if checksum == sum:
            checksum_status = True

        return {'data':data[0:6],'checksum':checksum_status}
 
    def __write(self,data):
        sum = 0
        for i in range(0,4):
            sum = sum + ord(data[i])
        part1 = chr((int(sum/127)))
        part2 = chr(sum % 127)
        command = (data+part1+part2).encode('ascii')
        self.serial.write(command)

    def adc(self,pin):
        command = "ra{}0".format(pin)
        self.__write(command)
        data = self.__read()
        value = int(data['data'][2:6])*self.__adcnum
        print(value)

    def digital_pin(self,pin,type='r',value=False):
        command = "{}d{}{}".format(type,chr(48+pin),chr(48+int(value)))
        self.__write(command)
        time.sleep(1)
        return self.__read()

#arduino = ARDUINO({'terminal':'/dev/ttyUSB0','baudrate':115200,'timeout':2,'adc':{'voltage':5,'bit':10}})

#arduino.digital_pin(13,'w',True)
#print(arduino.digital_pin(3,'w',True))
#arduino.digital_pin(4,'w',True)
#arduino.digital_pin(5,'w',True)
#arduino.digital_pin(6,'w',True)
#arduino.digital_pin(7,'w',True)
#arduino.digital_pin(7,'w',False)
#arduino.digital_pin(7,'w',True)
#arduino.digital_pin(7,'w',False)

#while True:
#    print(arduino.adc(1))
##print(arduino.read())
##print(arduino.read())
