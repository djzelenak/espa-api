import os

from api.providers.caching import CachingProviderInterfaceV0

import memcache


class CachingProviderException(Exception):
    pass


class CachingProvider(CachingProviderInterfaceV0):

    def __init__(self, memcache_hosts):
        if not memcache_hosts:
            memcache_hosts = os.getenv('ESPA_MEMCACHE_HOST', '127.0.0.1:11211').split(',')
        self.cache = memcache.Client(memcache_hosts, debug=0)
        self.timeout = 600 # 10 minutes

    def get(self, cache_key):
        return self.cache.get(cache_key)

    def set(self, cache_key, value, expirey=None):
        timeout = expirey or self.timeout
        self.cache.set(cache_key, value, timeout)
        return True
