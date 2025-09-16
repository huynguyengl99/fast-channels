import asyncio

import pytest_asyncio
from fast_channels.layers import register_channel_layer, unregister_channel_layer
from fast_channels.layers.redis import (
    RedisChannelLayer,
    RedisPubSubChannelLayer,
)


@pytest_asyncio.fixture
async def redis_limit_capacity_layer(wid, get_redis_host):
    layer = RedisChannelLayer(
        hosts=[get_redis_host(wid)], capacity=3, channel_capacity={"one": 1}
    )
    register_channel_layer("redis-limit", layer)
    yield layer
    await layer.flush()
    unregister_channel_layer("redis-limit")


@pytest_asyncio.fixture
async def redis_early_expire_layer(wid, get_redis_host):
    layer = RedisChannelLayer(hosts=[get_redis_host(wid)], expiry=3)
    register_channel_layer("redis-early", layer)
    yield layer
    await layer.flush()
    unregister_channel_layer("redis-early")


@pytest_asyncio.fixture
async def redis_multi_hosts_layer(wid, get_redis_host):
    hosts = [get_redis_host(wid + i * 5) for i in range(3)]

    layer = RedisChannelLayer(hosts=hosts, capacity=3)
    register_channel_layer("redis-multi", layer)
    yield layer
    await layer.flush()
    unregister_channel_layer("redis-multi")


@pytest_asyncio.fixture()
async def redis_pubsub_layer(wid, get_redis_host):
    """
    Channel layer fixture that flushes automatically.
    """

    layer = RedisPubSubChannelLayer(
        hosts=[get_redis_host(wid)], capacity=3, channel_capacity={"one": 1}
    )
    register_channel_layer("redis-pubsub", layer)
    yield layer
    async with asyncio.timeout(1):
        await layer.flush()
        unregister_channel_layer("redis-pubsub")


@pytest_asyncio.fixture()
async def other_pubsub_layer(wid, get_redis_host):
    """
    Channel layer fixture that flushes automatically.
    """

    layer = RedisPubSubChannelLayer(
        hosts=[get_redis_host(wid)], capacity=3, channel_capacity={"one": 1}
    )
    register_channel_layer("redis-pubsub2", layer)
    yield layer
    await layer.flush()
    unregister_channel_layer("redis-pubsub2")
