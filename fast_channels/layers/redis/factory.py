from .core import RedisChannelLayer
from .pubsub import RedisPubSubChannelLayer


def create_redis_channel_layer(
    redis_url: str = "redis://localhost:6379",
    prefix: str = "fastws",
    use_pubsub: bool = False,
    **kwargs,
) -> RedisChannelLayer | RedisPubSubChannelLayer:
    """
    Create a Redis channel layer instance.

    Args:
        redis_url: Redis connection URL
        prefix: Prefix for Redis keys
        use_pubsub: If True, use pub/sub layer, otherwise use queue-based layer
        **kwargs: Additional configuration options

    Returns:
        Configured Redis channel layer
    """
    config = {"hosts": [redis_url], "prefix": prefix, **kwargs}

    if use_pubsub:
        return RedisPubSubChannelLayer(**config)
    else:
        return RedisChannelLayer(**config)
