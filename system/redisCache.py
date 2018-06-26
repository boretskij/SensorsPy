import redis

class Redis:

    def __init__(self,config={'host':'localhost','port':6379,'db':0}):
        self.host = config['host']
        self.port = config['port']
        self.db = config['db']
        self.redis = self.connect()

    def connect(self):
        return redis.StrictRedis(host=self.host, port=self.port, db=self.db)

    ## Return array
    def get(self,keys):
        return self.redis.mget(keys)

    def set(self,key,data):
        self.redis.set(key,data)

    def keys(self,pattern="*"):
        return self.redis.keys(pattern)

