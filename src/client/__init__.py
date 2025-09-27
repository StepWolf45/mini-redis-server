"""
Клиент для mini-redis-server.
"""
from .client import RedisClient, RedisError

__all__ = ['RedisClient', 'RedisError']