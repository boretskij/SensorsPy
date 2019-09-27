import logging
import asyncio

from hbmqtt.client import MQTTClient, ClientException
from hbmqtt.mqtt.constants import QOS_0, QOS_1, QOS_2

import time

class MQTT:

    __root = '#'

    __topics = {}

    def __init__(self,configuration):
        self.host = configuration['host']
        self.client_id = "yellowline.online" if 'client_id' not in configuration else configuration['client_id']
        self.default_publish = configuration['default_publish']
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
               yield from self.connect.ping()
               yield from asyncio.sleep(2)

    @asyncio.coroutine
    def publish(self,topic,message,qos=QOS_2):
        if topic == '':
            topic = self.default_publish
        yield from self.connect.publish(topic, message.encode(),qos=qos)

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
            if topic in self.__topics:
                self.__topics[topic]['callback'](self.publish,{"topic":topic,"data":packet.payload.data})
            elif self.__root in self.__topics:
                self.__topics[self.__root]['callback'](self.publish,{"topic":topic,"data":packet.payload.data})

    @asyncio.coroutine
    def __connect(self):
        connect = MQTTClient(config={'keep_alive': 3600,'ping_delay':10,'reconnect_retries':30,'reconnect_max_interval':10,'auto_reconnect':True},client_id=self.client_id)
        yield from connect.connect(self.host)
        self.connect = connect

    def __reconnect(self,config):
        self.reconnect()

    def __disconnect(self):
        self.loop.run_until_complete(self.connect.disconnect())

# def main_function(content):
#     print("Me: " + str(content))

#if __name__ == "__main__":
#    loop = asyncio.get_event_loop()
#    mqtt = MQTT({'host':'mqtt://guest:guest@mqtt.meteostation.online'})
#    loop.run_until_complete(mqtt.init())
#    asyncio.ensure_future(mqtt.subscribe('/World',main_function))
#    asyncio.ensure_future(mqtt.handler())
#    asyncio.ensure_future(mqtt.monitor())
#    loop.run_forever()
