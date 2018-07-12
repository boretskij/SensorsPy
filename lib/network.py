import json
import urllib.request as urllib

class HTTPReq:

    def get(self,url):
        url = urllib.urlopen(url)
        return url.read()

    def post_json(self,url,content):
        request = urllib.Request(url)
        request.add_header("Content-Type","application/json; charset=utf-8")
        jdata = json.dumps(content).encode("utf-8")
        request.add_header("Content-Length", len(jdata))
        result = urllib.urlopen(request,jdata)
        return result
    
    def post_binary(self,url,binary_data):
        request = urllib.Request(url,binary_data)
        request.add_header('Content-Length','%d' % len(binary_data))
        request.add_header('Content-Type','application/octet-stream')
        result = urllib.urlopen(request)
        return result

#http = HTTPReq()
##print(http.get("https://checkip.amazonaws.com/"))
