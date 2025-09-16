import os
from collections.abc import Callable

import pytest
import pytest_asyncio
from fast_channels.layers import (
    InMemoryChannelLayer,
    register_channel_layer,
    unregister_channel_layer,
)
from fast_channels.layers.redis import RedisChannelLayer

redis_url = os.getenv("REDIS_URL", "redis://localhost:6399")


@pytest.fixture(scope="session")
def get_redis_host() -> Callable[[int], str]:
    def _get_redis_host(idx: int) -> str:
        return f"{redis_url}/{idx}"

    return _get_redis_host


@pytest.fixture(scope="session")
def wid(worker_id):
    if worker_id == "master":
        wid = 0
    else:
        wid = int(worker_id.replace("gw", "")) % 16
    return wid


@pytest_asyncio.fixture
async def redis_layer(wid, get_redis_host):
    layer = RedisChannelLayer(
        hosts=[get_redis_host(wid)], capacity=3, channel_capacity={"tiny": 1}
    )
    register_channel_layer("redis", layer)
    yield layer
    await layer.flush()
    unregister_channel_layer("redis")


def pytest_configure():
    register_channel_layer("inmemory", InMemoryChannelLayer())
