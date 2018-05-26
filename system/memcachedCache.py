import memcache


class Memcache:

    def __init__(self,configuration):
        return memcache.Client(ip=configuration['ip'],debug=configuration['debug'])        
