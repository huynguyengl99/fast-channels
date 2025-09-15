"""
Channel layer definitions and registration.
This file centralizes all channel layer configuration for the application.
"""

import os

from fast_channels.layers import InMemoryChannelLayer
from fast_channels.layers.redis import create_redis_channel_layer
from fast_channels.layers.registry import register_channel_layer

redis_url = os.getenv("REDIS_URL", "redis://localhost:6399")


def setup_layers():
    """
    Set up and register all channel layers for the application.
    This should be called once during application startup.
    """
    # Get Redis URL from environment or use default

    # Create different types of layers
    layers_config = {
        # In-memory layer for development/testing
        "memory": {
            "layer": InMemoryChannelLayer(),
            "description": "In-memory layer for development",
        },
        # Redis Pub/Sub layer for real-time messaging
        "chat": {
            "layer": create_redis_channel_layer(
                redis_url=redis_url,
                prefix="chat",
                use_pubsub=True,  # Fast pub/sub for chat
                expiry=300,  # 5 minutes
            ),
            "description": "Redis pub/sub layer for chat applications",
        },
        # Redis Queue layer for reliable messaging
        "queue": {
            "layer": create_redis_channel_layer(
                redis_url=redis_url,
                prefix="queue",
                use_pubsub=False,  # Reliable queue-based
                expiry=900,  # 15 minutes
                capacity=1000,
            ),
            "description": "Redis queue layer for reliable messaging",
        },
        # Notifications layer with different prefix
        "notifications": {
            "layer": create_redis_channel_layer(
                redis_url=redis_url,
                prefix="notify",
                use_pubsub=True,
                expiry=60,  # 1 minute (notifications are ephemeral)
            ),
            "description": "Redis pub/sub layer for notifications",
        },
        # Analytics layer for metrics/events
        "analytics": {
            "layer": create_redis_channel_layer(
                redis_url=redis_url,
                prefix="analytics",
                use_pubsub=False,  # Queue for reliability
                expiry=3600,  # 1 hour
                capacity=5000,
            ),
            "description": "Redis queue layer for analytics events",
        },
    }

    # Register all layers
    for alias, config in layers_config.items():
        register_channel_layer(alias, config["layer"])
