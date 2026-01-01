import redis
from ..core.config import settings
import logging

logger = logging.getLogger(__name__)

# Create Redis client - connection is lazy (happens on first use)
redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
)

# Test connection on first import (optional - won't crash app if Redis is down)
try:
    redis_client.ping()
    logger.info(f"Redis connected: {settings.redis_host}:{settings.redis_port}")
except Exception as e:
    logger.warning(f"Redis not available at startup: {e}. Session features will be unavailable.")
    # Don't raise - allow app to start even if Redis is down