import asyncio

import pytest
from fast_channels.exceptions import ChannelFull
from fast_channels.layers import (
    InMemoryChannelLayer,
    get_channel_layer,
    register_channel_layer,
    unregister_channel_layer,
)


@pytest.mark.asyncio
async def test_send_receive():
    """
    Makes sure we can send a message to a normal channel then receive it.
    """
    channel_layer = get_channel_layer("inmemory")

    await channel_layer.send(
        "test-channel-1", {"type": "test.message", "text": "Ahoy-hoy!"}
    )
    await channel_layer.send(
        "test-channel-1", {"type": "test.message", "text": "Ahoy-hoy!"}
    )
    message = await channel_layer.receive("test-channel-1")
    assert message["type"] == "test.message"
    assert message["text"] == "Ahoy-hoy!"
    # not removed because not empty
    assert "test-channel-1" in channel_layer.channels
    message = await channel_layer.receive("test-channel-1")
    assert message["type"] == "test.message"
    assert message["text"] == "Ahoy-hoy!"
    # removed because empty
    assert "test-channel-1" not in channel_layer.channels


@pytest.mark.asyncio
async def test_race_empty():
    """
    Makes sure the race is handled gracefully.
    """
    channel_layer = get_channel_layer("inmemory")

    receive_task = asyncio.create_task(channel_layer.receive("test-channel-1"))
    await asyncio.sleep(0.1)
    await channel_layer.send(
        "test-channel-1", {"type": "test.message", "text": "Ahoy-hoy!"}
    )
    del channel_layer.channels["test-channel-1"]
    await asyncio.sleep(0.1)
    message = await receive_task
    assert message["type"] == "test.message"
    assert message["text"] == "Ahoy-hoy!"


@pytest.mark.asyncio
async def test_send_capacity():
    """
    Makes sure we get ChannelFull when we hit the send capacity
    """
    register_channel_layer("inmemory-limit", InMemoryChannelLayer(capacity=3))

    channel_layer = get_channel_layer("inmemory-limit")

    await channel_layer.send("test-channel-1", {"type": "test.message"})
    await channel_layer.send("test-channel-1", {"type": "test.message"})
    await channel_layer.send("test-channel-1", {"type": "test.message"})
    with pytest.raises(ChannelFull):
        await channel_layer.send("test-channel-1", {"type": "test.message"})

    unregister_channel_layer("inmemory-limit")


@pytest.mark.asyncio
async def test_process_local_send_receive():
    """
    Makes sure we can send a message to a process-local channel then receive it.
    """
    channel_layer = get_channel_layer("inmemory")

    channel_name = await channel_layer.new_channel()
    await channel_layer.send(
        channel_name, {"type": "test.message", "text": "Local only please"}
    )
    message = await channel_layer.receive(channel_name)
    assert message["type"] == "test.message"
    assert message["text"] == "Local only please"


@pytest.mark.asyncio
async def test_multi_send_receive():
    """
    Tests overlapping sends and receives, and ordering.
    """
    channel_layer = get_channel_layer("inmemory")

    await channel_layer.send("test-channel-3", {"type": "message.1"})
    await channel_layer.send("test-channel-3", {"type": "message.2"})
    await channel_layer.send("test-channel-3", {"type": "message.3"})
    assert (await channel_layer.receive("test-channel-3"))["type"] == "message.1"
    assert (await channel_layer.receive("test-channel-3"))["type"] == "message.2"
    assert (await channel_layer.receive("test-channel-3"))["type"] == "message.3"


@pytest.mark.asyncio
async def test_groups_basic():
    """
    Tests basic group operation.
    """
    channel_layer = get_channel_layer("inmemory")

    await channel_layer.group_add("test-group", "test-gr-chan-1")
    await channel_layer.group_add("test-group", "test-gr-chan-2")
    await channel_layer.group_add("test-group", "test-gr-chan-3")
    await channel_layer.group_discard("test-group", "test-gr-chan-2")
    await channel_layer.group_send("test-group", {"type": "message.1"})
    # Make sure we get the message on the two channels that were in
    async with asyncio.timeout(1):
        assert (await channel_layer.receive("test-gr-chan-1"))["type"] == "message.1"
        assert (await channel_layer.receive("test-gr-chan-3"))["type"] == "message.1"
    # Make sure the removed channel did not get the message
    with pytest.raises(asyncio.TimeoutError):
        async with asyncio.timeout(1):
            await channel_layer.receive("test-gr-chan-2")


@pytest.mark.asyncio
async def test_groups_channel_full():
    """
    Tests that group_send ignores ChannelFull
    """
    channel_layer = get_channel_layer("inmemory")

    await channel_layer.group_add("test-group", "test-gr-chan-1")
    await channel_layer.group_send("test-group", {"type": "message.1"})
    await channel_layer.group_send("test-group", {"type": "message.1"})
    await channel_layer.group_send("test-group", {"type": "message.1"})
    await channel_layer.group_send("test-group", {"type": "message.1"})
    await channel_layer.group_send("test-group", {"type": "message.1"})


@pytest.mark.asyncio
async def test_expiry_single():
    """
    Tests that a message can expire.
    """
    channel_layer = InMemoryChannelLayer(expiry=0.1)
    await channel_layer.send("test-channel-1", {"type": "message.1"})
    assert len(channel_layer.channels) == 1

    await asyncio.sleep(0.1)

    # Message should have expired and been dropped.
    with pytest.raises(asyncio.TimeoutError):
        async with asyncio.timeout(0.5):
            await channel_layer.receive("test-channel-1")

    # Channel should be cleaned up.
    assert len(channel_layer.channels) == 0


@pytest.mark.asyncio
async def test_expiry_unread():
    """
    Tests that a message on a channel can expire and be cleaned up even if
    the channel is not read from again.
    """
    channel_layer = InMemoryChannelLayer(expiry=0.1)
    await channel_layer.send("test-channel-1", {"type": "message.1"})

    await asyncio.sleep(0.1)

    await channel_layer.send("test-channel-2", {"type": "message.2"})
    assert len(channel_layer.channels) == 2
    assert (await channel_layer.receive("test-channel-2"))["type"] == "message.2"
    # Both channels should be cleaned up.
    assert len(channel_layer.channels) == 0


@pytest.mark.asyncio
async def test_expiry_multi():
    """
    Tests that multiple messages can expire.
    """
    channel_layer = InMemoryChannelLayer(expiry=0.1)
    await channel_layer.send("test-channel-1", {"type": "message.1"})
    await channel_layer.send("test-channel-1", {"type": "message.2"})
    await channel_layer.send("test-channel-1", {"type": "message.3"})
    assert (await channel_layer.receive("test-channel-1"))["type"] == "message.1"

    await asyncio.sleep(0.1)
    await channel_layer.send("test-channel-1", {"type": "message.4"})
    assert (await channel_layer.receive("test-channel-1"))["type"] == "message.4"

    # The second and third message should have expired and been dropped.
    with pytest.raises(asyncio.TimeoutError):
        async with asyncio.timeout(0.5):
            await channel_layer.receive("test-channel-1")

    # Channel should be cleaned up.
    assert len(channel_layer.channels) == 0
