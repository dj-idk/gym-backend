import json
import functools
from datetime import datetime
from typing import Callable, Any, Optional

import redis

from src.config import settings
from .logging import logger


class PydanticJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Pydantic models, SQLAlchemy models, and datetime objects"""

    def default(self, obj):
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        elif hasattr(obj, "dict"):
            return obj.dict()
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, "__table__"):
            return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
        return super().default(obj)


try:
    redis_client = redis.Redis.from_url(
        url=settings.redis_url,
        decode_responses=True,
        socket_timeout=5,
        socket_connect_timeout=5,
    )
    redis_client.ping()
    logger.info("Redis connection established successfully")
except Exception as e:
    logger.error(f"Failed to connect to Redis: {str(e)}")
    redis_client = None


def serialize_data(data: Any) -> Optional[str]:
    """Serialize data using the custom JSON encoder"""
    if data is None:
        return None

    try:
        return json.dumps(data, cls=PydanticJSONEncoder)
    except Exception as e:
        logger.error(f"Serialization error: {str(e)}")
        return None


def deserialize_data(data_str: str) -> Any:
    """Deserialize data from JSON string"""
    if not data_str:
        return None

    try:
        return json.loads(data_str)
    except Exception as e:
        logger.error(f"Deserialization error: {str(e)}")
        return None


def generate_cache_key(func_name: str, kwargs: dict) -> str:
    """Generate a cache key based on function name and arguments"""
    filtered_kwargs = {
        k: v for k, v in kwargs.items() if k != "session" and not str(v).startswith("<")
    }

    key_parts = [func_name]

    if filtered_kwargs:
        for k, v in sorted(filtered_kwargs.items()):
            key_parts.append(f"{k}:{v}")

    return f"gym_backend:{':'.join(key_parts)}"


def redis_cache(expire_seconds: int = 3000):
    """
    A decorator that caches the result of a function in Redis.

    Args:
        expire_seconds: Time in seconds for the cache to expire
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if redis_client is None:
                logger.warning("Redis not available, skipping cache")
                return await func(*args, **kwargs)

            # Generate cache key
            cache_key = generate_cache_key(func.__name__, kwargs)
            logger.info(f"Cache key: {cache_key}")

            try:
                cached_result = redis_client.get(cache_key)
                if cached_result:
                    logger.info(f"Cache hit for {cache_key}")
                    result = deserialize_data(cached_result)
                    if result is not None:
                        return result
                    logger.warning(f"Could not deserialize cached data for {cache_key}")
                else:
                    logger.info(f"Cache miss for {cache_key}")
            except Exception as e:
                logger.error(f"Error retrieving from cache: {str(e)}")

            result = await func(*args, **kwargs)

            try:
                if result is not None:
                    serialized = serialize_data(result)
                    if serialized:
                        redis_client.setex(
                            name=cache_key, time=expire_seconds, value=serialized
                        )
                        logger.info(
                            f"Cached result for {cache_key} (expires in {expire_seconds}s)"
                        )
            except Exception as e:
                logger.error(f"Error caching result: {str(e)}")
                import traceback

                logger.error(traceback.format_exc())

            return result

        return wrapper

    return decorator


async def invalidate_public_cache():
    """Invalidate all public-facing cache entries"""
    if redis_client is None:
        logger.warning("Redis not available, cannot invalidate cache")
        return False

    try:
        pattern = "gym_backend:read_*"
        cursor = 0
        deleted_count = 0

        while True:
            cursor, keys = redis_client.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                deleted_count += redis_client.delete(*keys)
            if cursor == 0:
                break

        logger.info(f"Invalidated {deleted_count} cache entries")
        return True
    except Exception as e:
        logger.error(f"Error invalidating cache: {str(e)}")
        return False


def clear_all_cache():
    """Clear all keys in the Redis database"""
    if redis_client is None:
        logger.warning("Redis not available, cannot clear cache")
        return False

    try:
        redis_client.flushdb()
        logger.info("Redis cache cleared successfully")
        return True
    except Exception as e:
        logger.error(f"Error clearing Redis cache: {str(e)}")
        return False


def store_token_in_redis(
    token_id: str, admin_id: int, expires_at: datetime, additional_data: dict = None
):
    """
    Store token information in Redis with automatic expiration

    Args:
        token_id: The JWT token ID (jti)
        admin_id: The admin ID associated with the token
        expires_at: When the token expires
        additional_data: Optional additional data to store with the token
    """
    if redis_client is None:
        logger.warning("Redis not available, skipping token storage in Redis")
        return False

    try:
        now = datetime.now(expires_at.tzinfo)
        ttl = int((expires_at - now).total_seconds())

        if ttl <= 0:
            logger.warning(f"Token {token_id} already expired, not storing in Redis")
            return False

        token_key = f"token:{token_id}"

        token_data = {
            "admin_id": admin_id,
            "is_revoked": False,
            "expires_at": expires_at.isoformat(),
        }

        if additional_data:
            token_data.update(additional_data)

        redis_client.setex(name=token_key, time=ttl, value=serialize_data(token_data))

        admin_tokens_key = f"admin_tokens:{admin_id}"
        redis_client.sadd(admin_tokens_key, token_id)

        logger.info(f"Stored token {token_id} in Redis (expires in {ttl}s)")
        return True
    except Exception as e:
        logger.error(f"Error storing token in Redis: {str(e)}")
        return False


def revoke_token_in_redis(token_id: str):
    """
    Mark a token as revoked in Redis

    Args:
        token_id: The JWT token ID (jti)
    """
    if redis_client is None:
        logger.warning("Redis not available, skipping token revocation in Redis")
        return False

    try:
        token_key = f"token:{token_id}"

        token_data_str = redis_client.get(token_key)
        if not token_data_str:
            logger.warning(f"Token {token_id} not found in Redis")
            return False

        token_data = deserialize_data(token_data_str)
        if token_data:
            token_data["is_revoked"] = True
            redis_client.set(name=token_key, value=serialize_data(token_data))
            logger.info(f"Revoked token {token_id} in Redis")
            return True

        return False
    except Exception as e:
        logger.error(f"Error revoking token in Redis: {str(e)}")
        return False


def check_token_in_redis(token_id: str) -> dict:
    """
    Check if a token is valid in Redis

    Args:
        token_id: The JWT token ID (jti)

    Returns:
        dict: Token data if valid, None if invalid or not found
    """
    if redis_client is None:
        logger.warning("Redis not available, skipping token check in Redis")
        return None

    try:
        token_key = f"token:{token_id}"
        token_data_str = redis_client.get(token_key)

        if not token_data_str:
            logger.info(f"Token {token_id} not found in Redis")
            return None

        token_data = deserialize_data(token_data_str)

        if not token_data:
            return None

        if token_data.get("is_revoked", False):
            logger.info(f"Token {token_id} is revoked")
            return None

        return token_data
    except Exception as e:
        logger.error(f"Error checking token in Redis: {str(e)}")
        return None
