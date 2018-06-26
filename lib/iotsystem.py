from .network import HTTPReq

## REST and MQTT
class ThingsBoard:
    __rest_device = "/api/v1/{}/telemetry"

    def __init__(self,config):
        self.url = config['url']
        self.devices = config['devices']
        self.protocol = config['protocol']
        self.http = HTTPReq

    def send_data(self,data):
        for device in self.devices:
            url = self.url+self.__rest_device.format(device)
            self.http.post_json(HTTPReq,url,data)

