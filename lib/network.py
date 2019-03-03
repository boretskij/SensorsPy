import json
import gzip
import urllib.request as urllib
import urllib.parse as urlparse

class HTTPReq:

    __auth = ""
    __attempt = 5

    def __init__(self,config={}):
        if (len(config)>0):
            self.__auth = config['auth_token']

    def get(self,url):
        request = urllib.Request(url)
        if self.__auth!="":
            request.add_header("Authorization",self.__auth)
        url = urllib.urlopen(request)
        return url.read()

    def post_json(self,url,content):
        request = urllib.Request(url)
        if self.__auth!="":
            request.add_header("Authorization",self.__auth)
        request.add_header("Content-Type","application/json; charset=utf-8")
        jdata = json.dumps(content).encode("utf-8")
        request.add_header("Content-Length", len(jdata))
        result = urllib.urlopen(request,jdata)
        return result

    def post_binary(self,url,binary_data,compress=False,attempt_number=0):
        if (attempt_number>=self.__attempt):
            return None

        source = binary_data

        if compress:
            source = gzip.compress(binary_data,compresslevel=9)

        request = urllib.Request(url,source)
        if self.__auth!="":
            request.add_header("Authorization",self.__auth)
        if compress:
            request.add_header('Content-Encoding', 'gzip')
        request.add_header('Content-Length','%d' % len(source))
        request.add_header('Content-Type','application/octet-stream')
        result = None
        try:
            result = urllib.urlopen(request)
        except:
            attempt_number +=1
            return self.post_binary(url,binary_data,compress,attempt_number)
        return result
