import urllib.request as urllib

class HTTPReq:

    def get(self,url):
        url = urllib.urlopen(url)
        return url.read()

http = HTTPReq()
print(http.get("https://checkip.amazonaws.com/"))

