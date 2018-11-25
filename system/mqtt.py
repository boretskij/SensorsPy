import logging
import asyncio

from hbmqtt.client import MQTTClient, ClientException
from hbmqtt.mqtt.constants import QOS_0, QOS_1, QOS_2

import time

class MQTT:

    __topics = {}

    def __init__(self,configuration):
        self.host = configuration['host']
        self.loop = asyncio.get_event_loop()
        self.status = True
        self.init()

    @asyncio.coroutine
    def init(self):
        yield from self.__connect()

    def connection_status(self):
        return self.connect.session.transitions.state

    @asyncio.coroutine
    def monitor(self):
        while True:
               topics = self.__topics
               for name in topics:
                   topic = topics[name]
                   if topic['subscribed']==False and self.connect.session.transitions.state == 'connected':
                       yield from self.subscribe(name,topic['callback'],topic['qos'])
                   elif self.connect.session.transitions.state!='connected':
                       topic['subscribed'] = False
               if self.connect.session.transitions.state !='connected' and self.status==True:
                  self.status = False
               elif self.connect.session.transitions.state == 'connected' and self.status==False:
                  self.status = True
               yield from asyncio.sleep(2)

#    @asyncio.coroutine
    def publish(self,topic,message,qos=QOS_0):
        self.connect.publish(topic, message.encode(),qos=qos)

    @asyncio.coroutine
    def subscribe(self,topic,callback,qos=QOS_0):
        self.__topics[topic] = {'qos':qos,'callback':callback,'subscribed':False}
        yield from self.connect.subscribe([(topic,QOS_1)])
        self.__topics[topic]['subscribed'] = True

    @asyncio.coroutine
    def handler(self):
        while True:
            message = yield from self.connect.deliver_message()
            packet = message.publish_packet
            topic = packet.variable_header.topic_name
            self.__topics[topic]['callback']({"topic":topic,"data":packet.payload.data})

    @asyncio.coroutine
    def __connect(self):
        connect = MQTTClient(config={'keep_alive': 10,'ping_delay': 1,'reconnect_retries':10000,'reconnect_max_interval':30})
        yield from connect.connect(self.host)
        self.connect = connect

    def __reconnect(self,config):
        self.reconnect()

    def __disconnect(self):
        self.loop.run_until_complete(self.connect.disconnect())

def main_function(content):
    print("Me: " + str(content))

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    mqtt = MQTT({'host':'mqtt://guest:guest@mqtt.meteostation.online'})
    loop.run_until_complete(mqtt.init())
    asyncio.ensure_future(mqtt.subscribe('/World',main_function))
    asyncio.ensure_future(mqtt.handler())
    asyncio.ensure_future(mqtt.monitor())
    loop.run_forever()
