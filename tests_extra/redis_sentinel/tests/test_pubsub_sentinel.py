import asyncio
import random

import pytest
from asgiref.sync import async_to_sync
from fast_channels.layers.redis.utils import close_redis


@pytest.mark.asyncio
async def test_send_receive(pubsub_sentinel_layer):
    """
    Makes sure we can send a message to a normal channel then receive it.
    """
    channel = await pubsub_sentinel_layer.new_channel()
    await pubsub_sentinel_layer.send(
        channel, {"type": "test.message", "text": "Ahoy-hoy!"}
    )
    message = await pubsub_sentinel_layer.receive(channel)
    assert message["type"] == "test.message"
    assert message["text"] == "Ahoy-hoy!"


@pytest.mark.asyncio
async def test_multi_send_receive(pubsub_sentinel_layer):
    """
    Tests overlapping sends and receives, and ordering.
    """
    channel = await pubsub_sentinel_layer.new_channel()
    await pubsub_sentinel_layer.send(channel, {"type": "message.1"})
    await pubsub_sentinel_layer.send(channel, {"type": "message.2"})
    await pubsub_sentinel_layer.send(channel, {"type": "message.3"})
    assert (await pubsub_sentinel_layer.receive(channel))["type"] == "message.1"
    assert (await pubsub_sentinel_layer.receive(channel))["type"] == "message.2"
    assert (await pubsub_sentinel_layer.receive(channel))["type"] == "message.3"


def test_multi_send_receive_sync(pubsub_sentinel_layer):
    event_loop = asyncio.new_event_loop()
    _await = event_loop.run_until_complete
    channel = _await(pubsub_sentinel_layer.new_channel())
    send = async_to_sync(pubsub_sentinel_layer.send)
    send(channel, {"type": "message.1"})
    send(channel, {"type": "message.2"})
    send(channel, {"type": "message.3"})
    assert _await(pubsub_sentinel_layer.receive(channel))["type"] == "message.1"
    assert _await(pubsub_sentinel_layer.receive(channel))["type"] == "message.2"
    assert _await(pubsub_sentinel_layer.receive(channel))["type"] == "message.3"
    event_loop.close()


@pytest.mark.asyncio
async def test_groups_basic(pubsub_sentinel_layer):
    """
    Tests basic group operation.
    """
    channel_name1 = await pubsub_sentinel_layer.new_channel(prefix="test-gr-chan-1")
    channel_name2 = await pubsub_sentinel_layer.new_channel(prefix="test-gr-chan-2")
    channel_name3 = await pubsub_sentinel_layer.new_channel(prefix="test-gr-chan-3")
    await pubsub_sentinel_layer.group_add("test-group", channel_name1)
    await pubsub_sentinel_layer.group_add("test-group", channel_name2)
    await pubsub_sentinel_layer.group_add("test-group", channel_name3)
    await pubsub_sentinel_layer.group_discard("test-group", channel_name2)
    await pubsub_sentinel_layer.group_send("test-group", {"type": "message.1"})
    # Make sure we get the message on the two channels that were in
    async with asyncio.timeout(1):
        assert (await pubsub_sentinel_layer.receive(channel_name1))[
            "type"
        ] == "message.1"
        assert (await pubsub_sentinel_layer.receive(channel_name3))[
            "type"
        ] == "message.1"
    # Make sure the removed channel did not get the message
    with pytest.raises(asyncio.TimeoutError):
        async with asyncio.timeout(1):
            await pubsub_sentinel_layer.receive(channel_name2)


@pytest.mark.asyncio
async def test_groups_same_prefix(pubsub_sentinel_layer):
    """
    Tests group_send with multiple channels with same channel prefix
    """
    channel_name1 = await pubsub_sentinel_layer.new_channel(prefix="test-gr-chan")
    channel_name2 = await pubsub_sentinel_layer.new_channel(prefix="test-gr-chan")
    channel_name3 = await pubsub_sentinel_layer.new_channel(prefix="test-gr-chan")
    await pubsub_sentinel_layer.group_add("test-group", channel_name1)
    await pubsub_sentinel_layer.group_add("test-group", channel_name2)
    await pubsub_sentinel_layer.group_add("test-group", channel_name3)
    await pubsub_sentinel_layer.group_send("test-group", {"type": "message.1"})

    # Make sure we get the message on the channels that were in
    async with asyncio.timeout(1):
        assert (await pubsub_sentinel_layer.receive(channel_name1))[
            "type"
        ] == "message.1"
        assert (await pubsub_sentinel_layer.receive(channel_name2))[
            "type"
        ] == "message.1"
        assert (await pubsub_sentinel_layer.receive(channel_name3))[
            "type"
        ] == "message.1"


@pytest.mark.asyncio
async def test_random_reset__channel_name(pubsub_sentinel_layer):
    """
    Makes sure resetting random seed does not make us reuse channel names.
    """
    random.seed(1)
    channel_name_1 = await pubsub_sentinel_layer.new_channel()
    random.seed(1)
    channel_name_2 = await pubsub_sentinel_layer.new_channel()

    assert channel_name_1 != channel_name_2


def test_serialize(pubsub_sentinel_layer):
    """
    Test default serialization method
    """
    message = {"a": True, "b": None, "c": {"d": []}}
    serialized = pubsub_sentinel_layer.serialize(message)
    assert isinstance(serialized, bytes)
    assert serialized == b"\x83\xa1a\xc3\xa1b\xc0\xa1c\x81\xa1d\x90"


def test_deserialize(pubsub_sentinel_layer):
    """
    Test default deserialization method
    """
    message = b"\x83\xa1a\xc3\xa1b\xc0\xa1c\x81\xa1d\x90"
    deserialized = pubsub_sentinel_layer.deserialize(message)

    assert isinstance(deserialized, dict)
    assert deserialized == {"a": True, "b": None, "c": {"d": []}}


def test_multi_event_loop_garbage_collection(pubsub_sentinel_layer):
    """
    Test loop closure layer flushing and garbage collection
    """
    assert len(pubsub_sentinel_layer._layers.values()) == 0
    async_to_sync(test_send_receive)(pubsub_sentinel_layer)
    assert len(pubsub_sentinel_layer._layers.values()) == 0


@pytest.mark.asyncio
async def test_receive_hang(pubsub_sentinel_layer):
    channel_name = await pubsub_sentinel_layer.new_channel(prefix="test-channel")
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(pubsub_sentinel_layer.receive(channel_name), timeout=1)


@pytest.mark.asyncio
async def test_auto_reconnect(pubsub_sentinel_layer):
    """
    Tests redis-py reconnect and resubscribe
    """
    channel_name1 = await pubsub_sentinel_layer.new_channel(prefix="test-gr-chan-1")
    channel_name2 = await pubsub_sentinel_layer.new_channel(prefix="test-gr-chan-2")
    channel_name3 = await pubsub_sentinel_layer.new_channel(prefix="test-gr-chan-3")
    await pubsub_sentinel_layer.group_add("test-group", channel_name1)
    await pubsub_sentinel_layer.group_add("test-group", channel_name2)
    await close_redis(pubsub_sentinel_layer._shards[0]._redis)
    await pubsub_sentinel_layer.group_add("test-group", channel_name3)
    await pubsub_sentinel_layer.group_discard("test-group", channel_name2)
    await close_redis(pubsub_sentinel_layer._shards[0]._redis)
    await asyncio.sleep(1)
    await pubsub_sentinel_layer.group_send("test-group", {"type": "message.1"})
    # Make sure we get the message on the two channels that were in
    async with asyncio.timeout(5):
        assert (await pubsub_sentinel_layer.receive(channel_name1))[
            "type"
        ] == "message.1"
        assert (await pubsub_sentinel_layer.receive(channel_name3))[
            "type"
        ] == "message.1"
    # Make sure the removed channel did not get the message
    with pytest.raises(asyncio.TimeoutError):
        async with asyncio.timeout(1):
            await pubsub_sentinel_layer.receive(channel_name2)
