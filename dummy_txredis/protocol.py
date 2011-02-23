####################################################################
# FILENAME: dummy_txredis/protocol.py
# PROJECT: Dummy txRedis
# DESCRIPTION: Dummy txRedis client and factory. Mimics the 
#              txRedis interfaces and Redis' behavior but implements
#              everything internally rather than connecting to an
#              actual Redis server.
# 
#              Useful for writing unit tests for Twisted apps
#              that rely on txRedis.
# 
#              NB: Does not yet implement the full txRedis/Redis
#                  command set. Please feel free to fork and improve.
#
#
####################################################################
# (C)2011 DigiTar, All Rights Reserved
# 
# Distributed under the BSD License
# 
# Redistribution and use in source and binary forms, with or without modification, 
#    are permitted provided that the following conditions are met:
#
#        * Redistributions of source code must retain the above copyright notice, 
#          this list of conditions and the following disclaimer.
#        * Redistributions in binary form must reproduce the above copyright notice, 
#          this list of conditions and the following disclaimer in the documentation 
#          and/or other materials provided with the distribution.
#        * Neither the name of DigiTar nor the names of its contributors may be
#          used to endorse or promote products derived from this software without 
#          specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY 
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES 
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT 
# SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, 
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED 
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR 
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN 
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH 
# DAMAGE.
####################################################################

import time
from twisted.internet.defer import succeed, Deferred
from twisted.internet import reactor

class DummyRedisClient(object):
    """Mimics a Redis protocol client."""
    
    def __init__(self, db=0, password=None, charset='utf8', errors='strict'):
        self._store = {}
        self._expiries = {}
        
        self.charset = charset
        self.db = db
        self._store[db] = {}
        self._expiries[db] = {}
        self.db_selected = True
        self.password = password
        self.errors = errors
    
    def _expired(self, key):
        if self._expiries[self.db].has_key(key) and \
           int(time.time()) > self._expiries[self.db][key]:
            self._expiries[self.db].pop(key)
            self._store[self.db].pop(key)
            return True
        
        return False
    
    def expire(self, key, ttl):
        self._expired(key)
        if not self._store[self.db].has_key(key):
            return succeed(None)
        self._expiries[self.db][key] = int(time.time()) + ttl
        return succeed(None)
    
    def ttl(self, key):
        self._expired(key)
        if not self._store[self.db].has_key(key):
            return succeed(None)
        return succeed(int(time.time()) - self._expiries[self.db][key])
    
    def exists(self, key):
        self._expired(key)
        return succeed(int(self._store[self.db].has_key(key)))
    
    def delete(self, *args):
        deleted = 0
        for arg in args:
            if self._store[self.db].has_key(arg):
                self._store[self.db].pop(arg)
                deleted = deleted + 1
                if self._expiries[self.db].has_key(arg):
                    self._expiries[self.db].pop(arg)
        
        return succeed(deleted)
    
    def hgetall(self, key):
        if not self._store[self.db].has_key(key):
            return succeed(None)
        self._expired(key)
        if not isinstance(self._store[self.db][key], dict):
            raise Exception("Not a hash-based key.")
        return succeed(self._store[self.db][key])
    
    def hget(self, key, field):
        if not self._store[self.db].has_key(key):
            return succeed(None)
        self._expired(key)
        if not isinstance(self._store[self.db][key], dict):
            raise Exception("Not a hash-based key.")
        if not self._store[self.db][key].has_key(field):
            return None
        return succeed({field : self._store[self.db][key][field]})
    
    def hmset(self, key, field_dict):
        self._expired(key)
        if not self._store[self.db].has_key(key) or \
           not isinstance(self._store[self.db][key], dict):
           self._store[self.db][key] = {}
        
        for field in field_dict.keys():
            self._store[self.db][key][field] = str(field_dict[field])
        
        return succeed(True)
    
    def hset(self, key, field, value):
        self._expired(key)
        if not self._store[self.db].has_key(key) or \
           not isinstance(self._store[self.db][key], dict):
           self._store[self.db][key] = {}
        
        self._store[self.db][key][field] = str(value)
        return succeed(True)
    
    def keys(self, pattern):
        try:
            match_end = pattern.index("*")
            if match_end == 0:
                match_end = -1
        except ValueError:
            match_end = None
        
        for key in self._store[self.db].keys():
            self._expired(key)
        
        key_list = []
        for key in self._store[self.db].keys():
            if match_end == -1:
                key_list.append(key)
            elif key[0:match_end] == pattern[0:match_end]:
                key_list.append(key)
        
        return succeed(key_list)
    
    def get(self, key):
        if not self._store[self.db].has_key(key):
            return succeed(None)
        self._expired(key)
        if not isinstance(self._store[self.db][key], str):
            raise Exception("Not a string-based key.")
        
        return succeed(self._store[self.db][key])
    
    def set(self, key, value):
        self._expired(key)
        self._store[self.db][key] = str(value)
        return succeed(True)
    
    def smembers(self, key):
        if not self._store[self.db].has_key(key):
            return succeed(None)
        self._expired(key)
        if not isinstance(self._store[self.db][key], set):
            raise Exception("Not a set-based key.")
        return succeed(self._store[self.db][key])
    
    def sismember(self, key, value):
        if not self._store[self.db].has_key(key):
            return succeed(None)
        self._expired(key)
        if not isinstance(self._store[self.db][key], set):
            raise Exception("Not a set-based key.")
        
        if value in self._store[self.db][key]:
            return succeed(True)
        else:
            return succeed(None)
    
    def sadd(self, key, value):
        self._expired(key)
        if not self._store[self.db].has_key(key) or \
           not isinstance(self._store[self.db][key], set):
           self._store[self.db][key] = set()
        
        self._store[self.db][key].add(value)
        return succeed(True)
    
    def select(self, db):
        self.db = db
        if not self._store.has_key(self.db):
            self._store[self.db] = {}
            self._expiries[self.db] = {}
        return succeed(True)


class DummyRedisFactory(object):
    """Mimics a Redis factory with the client connection instantiated."""
    
    
    def __init__(self, *args, **kwargs):
        self.client = DummyRedisClient()
        self._kwargs = kwargs
        self._args = args
        self.deferred = Deferred()
        self.client = DummyRedisClient(*self._args, **self._kwargs)
        self.client.factory = self
        
        reactor.callLater(0, self.deferred.callback, True)