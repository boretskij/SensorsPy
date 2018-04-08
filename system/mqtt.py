import logging
import asyncio

from hbmqtt.client import MQTTClient, ClientException
from hbmqtt.mqtt.constants import QOS_1, QOS_2

class MQTT:

    def __init__(self,configuration):
        self.host = configuration['host']
        self.secure = configuration['secure']
        if configuration['secure']==True:
            self.catype = configuration['catype']
            self.certificate = configuration[self.catype]
    
    def __connect(self):
        connect = MQTTClient()
        yield from connect.connect(self.host)

if __name__ == "__main__":
    mqtt = MQTT({'host':'mqtt://broker.mqttdashboard.com','secure':False})


