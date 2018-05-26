import os

class HostSystem:

    __temp_sources = ['/etc/armbianmonitor/datasources/soctemp',
                     '/sys/class/thermal/thermal_zone0/temp']

    def __init__(self):
        info  = os.uname()
        self.__info = {}
        self.__info['nodename'] = info.nodename
        self.__info['machine'] = info.machine

        self.__detect_temp_source__()

    def __detect_temp_source__(self):
        for source in self.__temp_sources:
            if os.path.isfile(source):
                self.temp_source = source
                break

##    def GetInfo():
## /sys/class/thermal/t

##host = HostSystem()
##host.detect_temp_source()
