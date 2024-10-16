from typing import Optional
import platform
import redis
from src.settings import settings


class RedisConfig:
    ssl_ca_certs: Optional[str]  # Type hint for the attribute

    def __init__(self):
        host = settings.REDIS_HOST
        port = settings.REDIS_PORT
        password = settings.REDIS_PASSWORD
        operating_system = platform.system()
        if operating_system == "Linux":
            self.ssl_ca_certs = "/etc/ssl/certs/ca-certificates.crt"
        elif operating_system == "Darwin":  
            self.ssl_ca_certs = "/etc/ssl/cert.pem"  
        else:
            raise ValueError(f"Unsupported operating system: {operating_system}")
        self.redis = redis.Redis(host=host, port=port, password=password, ssl=True, ssl_ca_certs=self.ssl_ca_certs)   

    def set_value(self, key, value, ex=None):
        self.redis.set(key, value, ex=ex)

    def get_value(self, key):
        return self.redis.get(key)

    def exists(self, key):
        return self.redis.exists(key)
