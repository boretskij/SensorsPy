import os

class ORANGEPI2GIOT:

    __template = {'battery_voltage':'/sys/devices/platform/rda-power/power_supply/battery/voltage_now'}

    def __init__(self):
        self.test = ""
        template = '/sys/devices/platform/regulator-rda.{}/regulator/regulator.{}/microvolts'
        for index in range(1,14):
            rda_index = index - 1
            regulator = 'regulator_{}'.format(index)
            self.__template[regulator] = template.format(rda_index,index)

    def get_data(self):
        response = {}
        for element in self.__template:
            f = open(self.__template[element])
            data = str(f.read().replace('\n',''))
            response[element] = data
        return response


#t = ORANGEPI2GIOT()
#print(t.get_data())
