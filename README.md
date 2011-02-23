Dummy txRedis client and factory. Mimics the txRedis interfaces and Redis' behavior but implements everything internally rather than connecting to an actual Redis server.
 
* Useful for writing unit tests for Twisted apps that rely on txRedis.

* __NB:__ Does not yet implement the full txRedis/Redis command set. Please feel free to fork and improve.