import asyncio
import inspect
import random

import pytest
from fast_channels.layers.redis.utils import close_redis


@pytest.mark.asyncio
async def test_send_receive(redis_pubsub_layer):
    """
    Makes sure we can send a message to a normal channel then receive it.
    """
    channel = await redis_pubsub_layer.new_channel()
    await redis_pubsub_layer.send(
        channel, {"type": "test.message", "text": "Ahoy-hoy!"}
    )
    message = await redis_pubsub_layer.receive(channel)
    assert message["type"] == "test.message"
    assert message["text"] == "Ahoy-hoy!"


@pytest.mark.asyncio
async def test_multi_send_receive(redis_pubsub_layer):
    """
    Tests overlapping sends and receives, and ordering.
    """
    channel = await redis_pubsub_layer.new_channel()
    await redis_pubsub_layer.send(channel, {"type": "message.1"})
    await redis_pubsub_layer.send(channel, {"type": "message.2"})
    await redis_pubsub_layer.send(channel, {"type": "message.3"})
    assert (await redis_pubsub_layer.receive(channel))["type"] == "message.1"
    assert (await redis_pubsub_layer.receive(channel))["type"] == "message.2"
    assert (await redis_pubsub_layer.receive(channel))["type"] == "message.3"


@pytest.mark.asyncio
async def test_groups_basic(redis_pubsub_layer):
    """
    Tests basic group operation.
    """
    channel_name1 = await redis_pubsub_layer.new_channel(prefix="test-gr-chan-1")
    channel_name2 = await redis_pubsub_layer.new_channel(prefix="test-gr-chan-2")
    channel_name3 = await redis_pubsub_layer.new_channel(prefix="test-gr-chan-3")
    await redis_pubsub_layer.group_add("test-group", channel_name1)
    await redis_pubsub_layer.group_add("test-group", channel_name2)
    await redis_pubsub_layer.group_add("test-group", channel_name3)
    await redis_pubsub_layer.group_discard("test-group", channel_name2)
    await redis_pubsub_layer.group_send("test-group", {"type": "message.1"})
    # Make sure we get the message on the two channels that were in
    async with asyncio.timeout(1):
        assert (await redis_pubsub_layer.receive(channel_name1))["type"] == "message.1"
        assert (await redis_pubsub_layer.receive(channel_name3))["type"] == "message.1"
    # Make sure the removed channel did not get the message
    with pytest.raises(asyncio.TimeoutError):
        async with asyncio.timeout(1):
            await redis_pubsub_layer.receive(channel_name2)


@pytest.mark.asyncio
async def test_groups_same_prefix(redis_pubsub_layer):
    """
    Tests group_send with multiple channels with same channel prefix
    """
    channel_name1 = await redis_pubsub_layer.new_channel(prefix="test-gr-chan")
    channel_name2 = await redis_pubsub_layer.new_channel(prefix="test-gr-chan")
    channel_name3 = await redis_pubsub_layer.new_channel(prefix="test-gr-chan")
    await redis_pubsub_layer.group_add("test-group", channel_name1)
    await redis_pubsub_layer.group_add("test-group", channel_name2)
    await redis_pubsub_layer.group_add("test-group", channel_name3)
    await redis_pubsub_layer.group_send("test-group", {"type": "message.1"})

    # Make sure we get the message on the channels that were in
    async with asyncio.timeout(1):
        assert (await redis_pubsub_layer.receive(channel_name1))["type"] == "message.1"
        assert (await redis_pubsub_layer.receive(channel_name2))["type"] == "message.1"
        assert (await redis_pubsub_layer.receive(channel_name3))["type"] == "message.1"


@pytest.mark.asyncio
async def test_receive_on_non_owned_general_channel(
    redis_pubsub_layer, other_pubsub_layer
):
    """
    Tests receive with general channel that is not owned by the layer
    """
    receive_started = asyncio.Event()

    async def receive():
        receive_started.set()
        return await other_pubsub_layer.receive("test-channel")

    receive_task = asyncio.create_task(receive())
    await receive_started.wait()
    await asyncio.sleep(0.1)  # Need to give time for "receive" to subscribe
    await redis_pubsub_layer.send("test-channel", "message.1")

    try:
        # Make sure we get the message on the channels that were in
        async with asyncio.timeout(1):
            assert await receive_task == "message.1"
    finally:
        receive_task.cancel()


@pytest.mark.asyncio
async def test_random_reset__channel_name(redis_pubsub_layer):
    """
    Makes sure resetting random seed does not make us reuse channel names.
    """
    random.seed(1)
    channel_name_1 = await redis_pubsub_layer.new_channel()
    random.seed(1)
    channel_name_2 = await redis_pubsub_layer.new_channel()

    assert channel_name_1 != channel_name_2


def test_serialize(redis_pubsub_layer):
    """
    Test default serialization method
    """
    message = {"a": True, "b": None, "c": {"d": []}}
    serialized = redis_pubsub_layer.serialize(message)
    assert isinstance(serialized, bytes)
    assert serialized == b"\x83\xa1a\xc3\xa1b\xc0\xa1c\x81\xa1d\x90"


def test_deserialize(redis_pubsub_layer):
    """
    Test default deserialization method
    """
    message = b"\x83\xa1a\xc3\xa1b\xc0\xa1c\x81\xa1d\x90"
    deserialized = redis_pubsub_layer.deserialize(message)

    assert isinstance(deserialized, dict)
    assert deserialized == {"a": True, "b": None, "c": {"d": []}}


@pytest.mark.asyncio
async def test_proxied_methods_coroutine_check(redis_pubsub_layer):
    # inspect.iscoroutinefunction does not work for partial functions
    # below Python 3.8.
    assert inspect.iscoroutinefunction(redis_pubsub_layer.send)


@pytest.mark.asyncio
async def test_receive_hang(redis_pubsub_layer):
    channel_name = await redis_pubsub_layer.new_channel(prefix="test-channel")
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(redis_pubsub_layer.receive(channel_name), timeout=1)


@pytest.mark.asyncio
async def test_auto_reconnect(redis_pubsub_layer):
    """
    Tests redis-py reconnect and resubscribe
    """
    channel_name1 = await redis_pubsub_layer.new_channel(prefix="test-gr-chan-1")
    channel_name2 = await redis_pubsub_layer.new_channel(prefix="test-gr-chan-2")
    channel_name3 = await redis_pubsub_layer.new_channel(prefix="test-gr-chan-3")
    await redis_pubsub_layer.group_add("test-group", channel_name1)
    await redis_pubsub_layer.group_add("test-group", channel_name2)
    await close_redis(redis_pubsub_layer._shards[0]._redis)
    await redis_pubsub_layer.group_add("test-group", channel_name3)
    await redis_pubsub_layer.group_discard("test-group", channel_name2)
    await close_redis(redis_pubsub_layer._shards[0]._redis)
    await asyncio.sleep(1)
    await redis_pubsub_layer.group_send("test-group", {"type": "message.1"})
    # Make sure we get the message on the two channels that were in
    async with asyncio.timeout(5):
        assert (await redis_pubsub_layer.receive(channel_name1))["type"] == "message.1"
        assert (await redis_pubsub_layer.receive(channel_name3))["type"] == "message.1"
    # Make sure the removed channel did not get the message
    with pytest.raises(asyncio.TimeoutError):
        async with asyncio.timeout(1):
            await redis_pubsub_layer.receive(channel_name2)


@pytest.mark.asyncio
async def test_discard_before_add(redis_pubsub_layer):
    channel_name = await redis_pubsub_layer.new_channel(prefix="test-channel")
    # Make sure that we can remove a group before it was ever added without crashing.
    await redis_pubsub_layer.group_discard("test-group", channel_name)
