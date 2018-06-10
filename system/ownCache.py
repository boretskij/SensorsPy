## Simple cache

class OwnCache:

    __cache = {}
    __save_interval = 10 ## In seconds

    def __init__(self,save_to_disk=0):
        self.save = save_to_disk

    def set(self,key,data):
        self.__cache[key] = data

    def get (self,key):
        data = None
        if key in self.__cache:
            data = self.__cache[key]

        return data

cache = OwnCache()
cache.set("hello",{"g":"g"})
print(cache.get("hello"))
