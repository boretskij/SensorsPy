import redis

class Redis:

    def __init__(self,config):
        self.host = config['host']
        self.port = config['port']
        self.db = config['db']
        self.redis = self.connect()

    def connect(self):
        return redis.StrictRedis(host=self.host, port=self.port, db=self.db)

    def set(self,key,data):
        self.redis.set(key,element)

##redis = Redis({'host':'localhost','port':6379,'db':0})

##for i in range(1000000):
##    redis.set(i,[{'test':'test'}])
##print(type('d'))
