from .network import HTTPReq

import base64

class InfluxDB:

    __templates = {"write":"{}://{}:{}/write?db={}"}

    def __init__(self,config):
        self.host = config['host']
        self.username = config['username']
        self.password = config['password']
        self.port = config['port']
        self.ssl = config['ssl']
        self.database = config['database']
        self.__prepare_templates();
        self.__prepare_auth();
        self.http = HTTPReq({'auth_token':self.auth})

    def __prepare_templates(self):
        http_prefix = "http"
        if self.ssl==True:
            http_prefix="https"

        self.__templates['write'] = self.__templates['write'].format(http_prefix,self.host,self.port,self.database)

    def __prepare_auth(self):
        auth = base64.b64encode("{}:{}".format(self.username,self.password).encode())
        self.auth = "Basic {}".format(auth.decode())

    def write_to_db(self,data):
        return self.http.post_binary(self.__templates['write'],data.encode())
