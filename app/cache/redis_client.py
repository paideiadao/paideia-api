import redis
from config import Config, Network

CFG = Config[Network]

redisClient = redis.Redis(
    host=CFG.redis_host,
    port=CFG.redis_port,
)
