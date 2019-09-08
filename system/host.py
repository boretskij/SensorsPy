import os
import socket
import fcntl
import struct

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
                
    def get_ip_address(self,ifname): # Thanks stackoverflow https://stackoverflow.com/questions/6243276/how-to-get-the-physical-interface-ip-address-from-an-interface/17667982 but added small modifications
        interface = ifname.encode()
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', interface[:15])
        )[20:24])

##    def GetInfo():
## /sys/class/thermal/t

##host = HostSystem()
##host.detect_temp_source()
