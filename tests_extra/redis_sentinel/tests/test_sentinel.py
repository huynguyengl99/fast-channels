import asyncio
import random

import pytest
from fast_channels.layers.redis.core import ChannelFull, RedisChannelLayer


async def send_three_messages_with_delay(channel_name, sentinel_layer, delay):
    await sentinel_layer.send(channel_name, {"type": "test.message", "text": "First!"})

    await asyncio.sleep(delay)

    await sentinel_layer.send(channel_name, {"type": "test.message", "text": "Second!"})

    await asyncio.sleep(delay)

    await sentinel_layer.send(channel_name, {"type": "test.message", "text": "Third!"})


async def group_send_three_messages_with_delay(group_name, sentinel_layer, delay):
    await sentinel_layer.group_send(
        group_name, {"type": "test.message", "text": "First!"}
    )

    await asyncio.sleep(delay)

    await sentinel_layer.group_send(
        group_name, {"type": "test.message", "text": "Second!"}
    )

    await asyncio.sleep(delay)

    await sentinel_layer.group_send(
        group_name, {"type": "test.message", "text": "Third!"}
    )


@pytest.mark.asyncio
async def test_send_receive(sentinel_layer):
    """
    Makes sure we can send a message to a normal channel then receive it.
    """
    await sentinel_layer.send(
        "test-channel-1", {"type": "test.message", "text": "Ahoy-hoy!"}
    )
    message = await sentinel_layer.receive("test-channel-1")
    assert message["type"] == "test.message"
    assert message["text"] == "Ahoy-hoy!"


@pytest.mark.asyncio
async def test_send_capacity(sentinel_layer):
    """
    Makes sure we get ChannelFull when we hit the send capacity
    """
    await sentinel_layer.send("test-channel-1", {"type": "test.message"})
    await sentinel_layer.send("test-channel-1", {"type": "test.message"})
    await sentinel_layer.send("test-channel-1", {"type": "test.message"})
    with pytest.raises(ChannelFull):
        await sentinel_layer.send("test-channel-1", {"type": "test.message"})


@pytest.mark.asyncio
async def test_send_specific_capacity(limit_sentinel_layer):
    """
    Makes sure we get ChannelFull when we hit the send capacity on a specific channel
    """
    await limit_sentinel_layer.send("one", {"type": "test.message"})
    with pytest.raises(ChannelFull):
        await limit_sentinel_layer.send("one", {"type": "test.message"})
    await limit_sentinel_layer.flush()


@pytest.mark.asyncio
async def test_process_local_send_receive(sentinel_layer):
    """
    Makes sure we can send a message to a process-local channel then receive it.
    """
    channel_name = await sentinel_layer.new_channel()
    await sentinel_layer.send(
        channel_name, {"type": "test.message", "text": "Local only please"}
    )
    message = await sentinel_layer.receive(channel_name)
    assert message["type"] == "test.message"
    assert message["text"] == "Local only please"


@pytest.mark.asyncio
async def test_multi_send_receive(sentinel_layer):
    """
    Tests overlapping sends and receives, and ordering.
    """
    await sentinel_layer.send("test-channel-3", {"type": "message.1"})
    await sentinel_layer.send("test-channel-3", {"type": "message.2"})
    await sentinel_layer.send("test-channel-3", {"type": "message.3"})
    assert (await sentinel_layer.receive("test-channel-3"))["type"] == "message.1"
    assert (await sentinel_layer.receive("test-channel-3"))["type"] == "message.2"
    assert (await sentinel_layer.receive("test-channel-3"))["type"] == "message.3"
    await sentinel_layer.flush()


@pytest.mark.asyncio
async def test_reject_bad_channel(sentinel_layer):
    """
    Makes sure sending/receiving on an invalic channel name fails.
    """
    with pytest.raises(TypeError):
        await sentinel_layer.send("=+135!", {"type": "foom"})
    with pytest.raises(TypeError):
        await sentinel_layer.receive("=+135!")


@pytest.mark.asyncio
async def test_reject_bad_client_prefix(sentinel_layer):
    """
    Makes sure receiving on a non-prefixed local channel is not allowed.
    """
    with pytest.raises(AssertionError):
        await sentinel_layer.receive("not-client-prefix!local_part")


@pytest.mark.asyncio
async def test_groups_basic(sentinel_layer):
    """
    Tests basic group operation.
    """
    channel_name1 = await sentinel_layer.new_channel(prefix="test-gr-chan-1")
    channel_name2 = await sentinel_layer.new_channel(prefix="test-gr-chan-2")
    channel_name3 = await sentinel_layer.new_channel(prefix="test-gr-chan-3")
    await sentinel_layer.group_add("test-group", channel_name1)
    await sentinel_layer.group_add("test-group", channel_name2)
    await sentinel_layer.group_add("test-group", channel_name3)
    await sentinel_layer.group_discard("test-group", channel_name2)
    await sentinel_layer.group_send("test-group", {"type": "message.1"})
    # Make sure we get the message on the two channels that were in
    async with asyncio.timeout(1):
        assert (await sentinel_layer.receive(channel_name1))["type"] == "message.1"
        assert (await sentinel_layer.receive(channel_name3))["type"] == "message.1"
    # Make sure the removed channel did not get the message
    with pytest.raises(asyncio.TimeoutError):
        async with asyncio.timeout(1):
            await sentinel_layer.receive(channel_name2)
    await sentinel_layer.flush()


@pytest.mark.asyncio
async def test_groups_channel_full(sentinel_layer):
    """
    Tests that group_send ignores ChannelFull
    """
    await sentinel_layer.group_add("test-group", "test-gr-chan-1")
    await sentinel_layer.group_send("test-group", {"type": "message.1"})
    await sentinel_layer.group_send("test-group", {"type": "message.1"})
    await sentinel_layer.group_send("test-group", {"type": "message.1"})
    await sentinel_layer.group_send("test-group", {"type": "message.1"})
    await sentinel_layer.group_send("test-group", {"type": "message.1"})
    await sentinel_layer.flush()


@pytest.mark.asyncio
async def test_groups_multiple_hosts(multiple_sentinel_layer):
    """
    Tests advanced group operation with multiple hosts.
    """
    channel_name1 = await multiple_sentinel_layer.new_channel(prefix="channel1")
    channel_name2 = await multiple_sentinel_layer.new_channel(prefix="channel2")
    channel_name3 = await multiple_sentinel_layer.new_channel(prefix="channel3")
    await multiple_sentinel_layer.group_add("test-group", channel_name1)
    await multiple_sentinel_layer.group_add("test-group", channel_name2)
    await multiple_sentinel_layer.group_add("test-group", channel_name3)
    await multiple_sentinel_layer.group_discard("test-group", channel_name2)
    await multiple_sentinel_layer.group_send("test-group", {"type": "message.1"})
    await multiple_sentinel_layer.group_send("test-group", {"type": "message.1"})

    # Make sure we get the message on the two channels that were in
    async with asyncio.timeout(1):
        assert (await multiple_sentinel_layer.receive(channel_name1))[
            "type"
        ] == "message.1"
        assert (await multiple_sentinel_layer.receive(channel_name3))[
            "type"
        ] == "message.1"

    with pytest.raises(asyncio.TimeoutError):
        async with asyncio.timeout(1):
            await multiple_sentinel_layer.receive(channel_name2)

    await multiple_sentinel_layer.flush()


@pytest.mark.asyncio
async def test_groups_same_prefix(sentinel_layer):
    """
    Tests group_send with multiple channels with same channel prefix
    """
    channel_name1 = await sentinel_layer.new_channel(prefix="test-gr-chan")
    channel_name2 = await sentinel_layer.new_channel(prefix="test-gr-chan")
    channel_name3 = await sentinel_layer.new_channel(prefix="test-gr-chan")
    await sentinel_layer.group_add("test-group", channel_name1)
    await sentinel_layer.group_add("test-group", channel_name2)
    await sentinel_layer.group_add("test-group", channel_name3)
    await sentinel_layer.group_send("test-group", {"type": "message.1"})

    # Make sure we get the message on the channels that were in
    async with asyncio.timeout(1):
        assert (await sentinel_layer.receive(channel_name1))["type"] == "message.1"
        assert (await sentinel_layer.receive(channel_name2))["type"] == "message.1"
        assert (await sentinel_layer.receive(channel_name3))["type"] == "message.1"

    await sentinel_layer.flush()


@pytest.mark.parametrize(
    "num_channels,timeout",
    [
        (1, 1),  # Edge cases - make sure we can send to a single channel
        (10, 1),
        (100, 10),
    ],
)
@pytest.mark.asyncio
async def test_groups_multiple_hosts_performance(
    multiple_sentinel_layer, num_channels, timeout
):
    """
    Tests advanced group operation: can send efficiently to multiple channels
    with multiple hosts within a certain timeout
    """
    channels = []
    for i in range(0, num_channels):
        channel = await multiple_sentinel_layer.new_channel(prefix=f"channel{i}")
        await multiple_sentinel_layer.group_add("test-group", channel)
        channels.append(channel)

    async with asyncio.timeout(timeout):
        await multiple_sentinel_layer.group_send("test-group", {"type": "message.1"})

    # Make sure we get the message all the channels
    async with asyncio.timeout(timeout):
        for channel in channels:
            assert (await multiple_sentinel_layer.receive(channel))[
                "type"
            ] == "message.1"

    await multiple_sentinel_layer.flush()


@pytest.mark.asyncio
async def test_group_send_capacity(sentinel_layer, caplog):
    """
    Makes sure we dont group_send messages to channels that are over capacity.
    Make sure number of channels with full capacity are logged as an exception to help debug errors.
    """

    channel = await sentinel_layer.new_channel()
    await sentinel_layer.group_add("test-group", channel)

    await sentinel_layer.group_send("test-group", {"type": "message.1"})
    await sentinel_layer.group_send("test-group", {"type": "message.2"})
    await sentinel_layer.group_send("test-group", {"type": "message.3"})
    await sentinel_layer.group_send("test-group", {"type": "message.4"})

    # We should receive the first 3 messages
    assert (await sentinel_layer.receive(channel))["type"] == "message.1"
    assert (await sentinel_layer.receive(channel))["type"] == "message.2"
    assert (await sentinel_layer.receive(channel))["type"] == "message.3"

    # Make sure we do NOT receive message 4
    with pytest.raises(asyncio.TimeoutError):
        async with asyncio.timeout(1):
            await sentinel_layer.receive(channel)

    # Make sure number of channels over capacity are logged
    for record in caplog.records:
        assert record.levelname == "INFO"
        assert (
            record.getMessage() == "1 of 1 channels over capacity in group test-group"
        )


@pytest.mark.asyncio
async def test_group_send_capacity_multiple_channels(sentinel_layer, caplog):
    """
    Makes sure we dont group_send messages to channels that are over capacity
    Make sure number of channels with full capacity are logged as an exception to help debug errors.
    """

    channel_1 = await sentinel_layer.new_channel()
    channel_2 = await sentinel_layer.new_channel(prefix="channel_2")
    await sentinel_layer.group_add("test-group", channel_1)
    await sentinel_layer.group_add("test-group", channel_2)

    # Let's put channel_2 over capacity
    await sentinel_layer.send(channel_2, {"type": "message.0"})

    await sentinel_layer.group_send("test-group", {"type": "message.1"})
    await sentinel_layer.group_send("test-group", {"type": "message.2"})
    await sentinel_layer.group_send("test-group", {"type": "message.3"})

    # Channel_1 should receive all 3 group messages
    assert (await sentinel_layer.receive(channel_1))["type"] == "message.1"
    assert (await sentinel_layer.receive(channel_1))["type"] == "message.2"
    assert (await sentinel_layer.receive(channel_1))["type"] == "message.3"

    # Channel_2 should receive the first message + 2 group messages
    assert (await sentinel_layer.receive(channel_2))["type"] == "message.0"
    assert (await sentinel_layer.receive(channel_2))["type"] == "message.1"
    assert (await sentinel_layer.receive(channel_2))["type"] == "message.2"

    # Make sure channel_2 does not receive the 3rd group message
    with pytest.raises(asyncio.TimeoutError):
        async with asyncio.timeout(1):
            await sentinel_layer.receive(channel_2)

    # Make sure number of channels over capacity are logged
    for record in caplog.records:
        assert record.levelname == "INFO"
        assert (
            record.getMessage() == "1 of 2 channels over capacity in group test-group"
        )


@pytest.mark.xfail(
    reason="""
Fails with error in redis-py: int() argument must be a string, a bytes-like
object or a real number, not 'NoneType'. Refs: #348
"""
)
@pytest.mark.asyncio
async def test_receive_cancel(sentinel_layer):
    """
    Makes sure we can cancel a receive without blocking
    """
    sentinel_layer = RedisChannelLayer(capacity=30)
    channel = await sentinel_layer.new_channel()
    delay = 0
    while delay < 0.01:
        await sentinel_layer.send(
            channel, {"type": "test.message", "text": "Ahoy-hoy!"}
        )

        task = asyncio.ensure_future(sentinel_layer.receive(channel))
        await asyncio.sleep(delay)
        task.cancel()
        delay += 0.0001

        try:
            await asyncio.wait_for(task, None)
        except asyncio.CancelledError:
            pass


@pytest.mark.asyncio
async def test_random_reset__channel_name(sentinel_layer):
    """
    Makes sure resetting random seed does not make us reuse channel names.
    """

    sentinel_layer = RedisChannelLayer()
    random.seed(1)
    channel_name_1 = await sentinel_layer.new_channel()
    random.seed(1)
    channel_name_2 = await sentinel_layer.new_channel()

    assert channel_name_1 != channel_name_2


@pytest.mark.asyncio
async def test_random_reset__client_prefix(sentinel_layer):
    """
    Makes sure resetting random seed does not make us reuse client_prefixes.
    """

    random.seed(1)
    channel_layer_1 = RedisChannelLayer()
    random.seed(1)
    channel_layer_2 = RedisChannelLayer()
    assert channel_layer_1.client_prefix != channel_layer_2.client_prefix


@pytest.mark.asyncio
async def test_message_expiry__earliest_message_expires(expiry_sentinel_layer):
    delay = 2
    channel_name = await expiry_sentinel_layer.new_channel()

    task = asyncio.ensure_future(
        send_three_messages_with_delay(channel_name, expiry_sentinel_layer, delay)
    )
    await asyncio.wait_for(task, None)

    # the first message should have expired, we should only see the second message and the third
    message = await expiry_sentinel_layer.receive(channel_name)
    assert message["type"] == "test.message"
    assert message["text"] == "Second!"

    message = await expiry_sentinel_layer.receive(channel_name)
    assert message["type"] == "test.message"
    assert message["text"] == "Third!"

    # Make sure there's no third message even out of order
    with pytest.raises(asyncio.TimeoutError):
        async with asyncio.timeout(1):
            await expiry_sentinel_layer.receive(channel_name)


@pytest.mark.asyncio
async def test_message_expiry__all_messages_under_expiration_time(
    expiry_sentinel_layer,
):
    delay = 1
    channel_name = await expiry_sentinel_layer.new_channel()

    task = asyncio.ensure_future(
        send_three_messages_with_delay(channel_name, expiry_sentinel_layer, delay)
    )
    await asyncio.wait_for(task, None)

    # expiry = 3, total delay under 3, all messages there
    message = await expiry_sentinel_layer.receive(channel_name)
    assert message["type"] == "test.message"
    assert message["text"] == "First!"

    message = await expiry_sentinel_layer.receive(channel_name)
    assert message["type"] == "test.message"
    assert message["text"] == "Second!"

    message = await expiry_sentinel_layer.receive(channel_name)
    assert message["type"] == "test.message"
    assert message["text"] == "Third!"


@pytest.mark.asyncio
async def test_message_expiry__group_send(expiry_sentinel_layer):
    delay = 2
    channel_name = await expiry_sentinel_layer.new_channel()

    await expiry_sentinel_layer.group_add("test-group", channel_name)

    task = asyncio.ensure_future(
        group_send_three_messages_with_delay("test-group", expiry_sentinel_layer, delay)
    )
    await asyncio.wait_for(task, None)

    # the first message should have expired, we should only see the second message and the third
    message = await expiry_sentinel_layer.receive(channel_name)
    assert message["type"] == "test.message"
    assert message["text"] == "Second!"

    message = await expiry_sentinel_layer.receive(channel_name)
    assert message["type"] == "test.message"
    assert message["text"] == "Third!"

    # Make sure there's no third message even out of order
    with pytest.raises(asyncio.TimeoutError):
        async with asyncio.timeout(1):
            await expiry_sentinel_layer.receive(channel_name)


@pytest.mark.xfail(reason="Fails with timeout. Refs: #348")
@pytest.mark.asyncio
async def test_message_expiry__group_send__one_channel_expires_message(
    expiry_sentinel_layer,
):
    delay = 1

    channel_1 = await expiry_sentinel_layer.new_channel()
    channel_2 = await expiry_sentinel_layer.new_channel(prefix="channel_2")

    await expiry_sentinel_layer.group_add("test-group", channel_1)
    await expiry_sentinel_layer.group_add("test-group", channel_2)

    # Let's give channel_1 one additional message and then sleep
    await expiry_sentinel_layer.send(
        channel_1, {"type": "test.message", "text": "Zero!"}
    )
    await asyncio.sleep(2)

    task = asyncio.ensure_future(
        group_send_three_messages_with_delay("test-group", expiry_sentinel_layer, delay)
    )
    await asyncio.wait_for(task, None)

    # message Zero! was sent about 2 + 1 + 1 seconds ago and it should have expired
    message = await expiry_sentinel_layer.receive(channel_1)
    assert message["type"] == "test.message"
    assert message["text"] == "First!"

    message = await expiry_sentinel_layer.receive(channel_1)
    assert message["type"] == "test.message"
    assert message["text"] == "Second!"

    message = await expiry_sentinel_layer.receive(channel_1)
    assert message["type"] == "test.message"
    assert message["text"] == "Third!"

    # Make sure there's no fourth message even out of order
    with pytest.raises(asyncio.TimeoutError):
        async with asyncio.timeout(1):
            await expiry_sentinel_layer.receive(channel_1)

    # channel_2 should receive all three messages from group_send
    message = await expiry_sentinel_layer.receive(channel_2)
    assert message["type"] == "test.message"
    assert message["text"] == "First!"

    # the first message should have expired, we should only see the second message and the third
    message = await expiry_sentinel_layer.receive(channel_2)
    assert message["type"] == "test.message"
    assert message["text"] == "Second!"

    message = await expiry_sentinel_layer.receive(channel_2)
    assert message["type"] == "test.message"
    assert message["text"] == "Third!"


def test_default_group_key_format():
    sentinel_layer = RedisChannelLayer()
    group_name = sentinel_layer._group_key("test_group")
    assert group_name == b"asgi:group:test_group"


def test_custom_group_key_format():
    sentinel_layer = RedisChannelLayer(prefix="test_prefix")
    group_name = sentinel_layer._group_key("test_group")
    assert group_name == b"test_prefix:group:test_group"


def test_receive_buffer_respects_capacity():
    sentinel_layer = RedisChannelLayer()
    buff = sentinel_layer.receive_buffer["test-group"]
    for i in range(10000):
        buff.put_nowait(i)

    capacity = 100
    assert sentinel_layer.capacity == capacity
    assert buff.full() is True
    assert buff.qsize() == capacity
    messages = [buff.get_nowait() for _ in range(capacity)]
    assert list(range(9900, 10000)) == messages


def test_serialize():
    """
    Test default serialization method
    """
    message = {"a": True, "b": None, "c": {"d": []}}
    sentinel_layer = RedisChannelLayer()
    serialized = sentinel_layer.serialize(message)
    assert isinstance(serialized, bytes)
    assert serialized[12:] == b"\x83\xa1a\xc3\xa1b\xc0\xa1c\x81\xa1d\x90"


def test_deserialize():
    """
    Test default deserialization method
    """
    message = b"Q\x0c\xbb?Q\xbc\xe3|D\xfd9\x00\x83\xa1a\xc3\xa1b\xc0\xa1c\x81\xa1d\x90"
    sentinel_layer = RedisChannelLayer()
    deserialized = sentinel_layer.deserialize(message)

    assert isinstance(deserialized, dict)
    assert deserialized == {"a": True, "b": None, "c": {"d": []}}
