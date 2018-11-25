from .network import HTTPReq

import urllib.parse as urlparse

import base64

class InfluxDB:

    __templates = {"write":"{}://{}:{}/write?db={}",
                    "read":"{}://{}:{}/query?db={}&q={}"}

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
        self.http_prefix = "http"
        if self.ssl==True:
            self.http_prefix="https"

        #self.__templates['read'] = self.__templates['read'].format(http_prefix,self.host,self.port,self.database,"query")
        self.__templates['write'] = self.__templates['write'].format(self.http_prefix,self.host,self.port,self.database)

    def __prepare_auth(self):
        auth = base64.b64encode("{}:{}".format(self.username,self.password).encode())
        self.auth = "Basic {}".format(auth.decode())

    def read_from_db(self,query):
        data = self.__templates['read'].format(self.http_prefix,self.host,self.port,self.database,urlparse.quote(query))
        return self.http.get(data)

    def write_to_db(self,data):
        return self.http.post_binary(self.__templates['write'],data.encode())
