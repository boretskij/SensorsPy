from .ownCache import OwnCache
from .redisCache import Redis
from .memcachedCache import Memcache

import datetime

class Cache:

    __priority = ["redis","memcache","own"]

    def __init__(self,cache_type="any",save_to_disk=0):
        self.save_data = save_to_disk
        self.type = cache_type
        self.__check_cache_connect()

    def __check_cache_connect(self):
        connector = None
        default_key = datetime.datetime.utcnow().timestamp()
        default_data = "Init cache"
        try:
            connector = Redis()
        except:
            try:
                connector = Memcache()
            except:
                try:
                    connector = OwnCache()
                except:
                    connector = None

        self.connector = connector

    def set(self,key,data):
        self.connector.set(key,data)
