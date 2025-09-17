import os

import pytest
import pytest_asyncio
from fast_channels.layers import register_channel_layer, unregister_channel_layer
from fast_channels.layers.redis import RedisChannelLayer, RedisPubSubChannelLayer

# Redis Sentinel configuration - use environment variables with defaults
# In CI with GitHub Actions services, the host is "localhost"
# In local Docker, the host is "redis-sentinel"
SENTINEL_HOST = os.getenv("REDIS_SENTINEL_HOST", "redis-sentinel")
SENTINEL_PORT = int(os.getenv("REDIS_SENTINEL_PORT", "26379"))
SENTINEL_MASTER = os.getenv("REDIS_SENTINEL_SERVICE_NAME", "sentinel")
SENTINEL_PASSWORD = os.getenv("REDIS_SENTINEL_PASSWORD", "channels_redis")

# Sentinel configuration
SENTINEL_KWARGS = {"password": SENTINEL_PASSWORD}
TEST_HOSTS = [
    {
        "sentinels": [(SENTINEL_HOST, SENTINEL_PORT)],
        "master_name": SENTINEL_MASTER,
        "sentinel_kwargs": SENTINEL_KWARGS,
    }
]


@pytest.fixture(scope="session")
def wid(worker_id):
    """Worker ID fixture for test isolation using different databases."""
    if worker_id == "master":
        wid = 0
    else:
        wid = int(worker_id.replace("gw", "")) % 16
    return wid


@pytest_asyncio.fixture
async def sentinel_layer(wid):
    """
    Redis Sentinel channel layer fixture that connects to the sentinel cluster.
    Uses wid as database number for test isolation.
    """
    hosts_config = TEST_HOSTS[0].copy()
    hosts_config["db"] = wid

    layer = RedisChannelLayer(
        hosts=[hosts_config],
        capacity=3,
        channel_capacity={"tiny": 1},
    )
    register_channel_layer("redis-sentinel", layer)
    yield layer
    await layer.flush()
    unregister_channel_layer("redis-sentinel")


@pytest_asyncio.fixture
async def limit_sentinel_layer(wid):
    """
    Redis Sentinel channel layer with multiple configurations for testing.
    Uses wid + 1 as database number for isolation from main layer.
    """
    hosts_config = TEST_HOSTS[0].copy()
    hosts_config["db"] = wid

    layer = RedisChannelLayer(
        hosts=[hosts_config],
        capacity=3,
        channel_capacity={"one": 1},
    )
    register_channel_layer("redis-limit-sentinel", layer)
    yield layer
    await layer.flush()
    unregister_channel_layer("redis-limit-sentinel")


@pytest_asyncio.fixture
async def multiple_sentinel_layer(wid):
    """
    Redis Sentinel channel layer fixture that connects to the sentinel cluster.
    Uses wid as database number for test isolation.
    """
    hosts_configs = []
    for i in range(3):
        host_config = TEST_HOSTS[0].copy()
        host_config["db"] = wid + i * 5
        hosts_configs.append(host_config)

    layer = RedisChannelLayer(
        hosts=hosts_configs,
        capacity=100,
    )
    register_channel_layer("redis-multi-sentinel", layer)
    yield layer
    await layer.flush()
    unregister_channel_layer("redis-multi-sentinel")


@pytest_asyncio.fixture
async def expiry_sentinel_layer(wid):
    """
    Redis Sentinel channel layer fixture that connects to the sentinel cluster.
    Uses wid as database number for test isolation.
    """
    hosts_config = TEST_HOSTS[0].copy()
    hosts_config["db"] = wid

    layer = RedisChannelLayer(
        hosts=[hosts_config],
        expiry=3,
    )
    register_channel_layer("redis-expiry-sentinel", layer)
    yield layer
    await layer.flush()
    unregister_channel_layer("redis-expiry-sentinel")


@pytest_asyncio.fixture
async def pubsub_sentinel_layer(wid):
    """
    Redis Sentinel channel layer fixture that connects to the sentinel cluster.
    Uses wid as database number for test isolation.
    """
    hosts_config = TEST_HOSTS[0].copy()
    hosts_config["db"] = wid

    layer = RedisPubSubChannelLayer(
        hosts=[hosts_config],
    )
    register_channel_layer("redis-pubsub-sentinel", layer)
    yield layer
    await layer.flush()
    unregister_channel_layer("redis-pubsub-sentinel")
