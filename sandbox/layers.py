"""
Channel layer definitions and registration.
This file centralizes all channel layer configuration for the application.
"""

import os

from fast_channels.layers import (
    InMemoryChannelLayer,
    register_channel_layer,
)
from fast_channels.layers.base import BaseChannelLayer
from fast_channels.layers.redis import (
    RedisChannelLayer,
    RedisPubSubChannelLayer,
)

redis_url = os.getenv("REDIS_URL", "redis://localhost:6399")


def setup_layers():
    """
    Set up and register all channel layers for the application.
    This should be called once during application startup.
    """
    # Get Redis URL from environment or use default

    # Create different types of layers
    layers_config: dict[str, BaseChannelLayer] = {
        # In-memory layer for development/testing
        "memory": InMemoryChannelLayer(),
        # Redis Pub/Sub layer for real-time messaging
        "chat": RedisPubSubChannelLayer(hosts=[redis_url], prefix="chat"),
        # Redis Queue layer for reliable messaging
        "queue": RedisChannelLayer(
            hosts=[redis_url],
            prefix="queue",
            expiry=900,  # 15 minutes
            capacity=1000,
        ),
        # Notifications layer with different prefix
        "notifications": RedisPubSubChannelLayer(hosts=[redis_url], prefix="notify"),
        # Analytics layer for metrics/events
        "analytics": RedisChannelLayer(
            hosts=[redis_url],
            prefix="analytics",
            expiry=3600,  # 1 hour
            capacity=5000,
        ),
    }

    # Register all layers
    for alias, layer in layers_config.items():
        register_channel_layer(alias, layer)
