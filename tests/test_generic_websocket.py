from typing import Any

import pytest
from fast_channels.consumer.websocket import (
    AsyncJsonWebsocketConsumer,
    AsyncWebsocketConsumer,
)
from fast_channels.layers import InMemoryChannelLayer, get_channel_layer
from fast_channels.testing import WebsocketCommunicator


@pytest.mark.asyncio
async def test_async_websocket_consumer():
    """
    Tests that AsyncWebsocketConsumer is implemented correctly.
    """
    results = {}

    class TestConsumer(AsyncWebsocketConsumer):
        async def connect(self):
            results["connected"] = True
            await self.accept()

        async def receive(self, text_data=None, bytes_data=None):
            results["received"] = (text_data, bytes_data)
            await self.send(text_data=text_data, bytes_data=bytes_data)

        async def disconnect(self, code):
            results["disconnected"] = code

    app = TestConsumer()

    # Test a normal connection
    communicator = WebsocketCommunicator(app, "/testws/")
    connected, _ = await communicator.connect()
    assert connected
    assert "connected" in results
    # Test sending text
    await communicator.send_to(text_data="hello")
    response = await communicator.receive_from()
    assert response == "hello"
    assert results["received"] == ("hello", None)
    # Test sending bytes
    await communicator.send_to(bytes_data=b"w\0\0\0")
    response = await communicator.receive_from()
    assert response == b"w\0\0\0"
    assert results["received"] == (None, b"w\0\0\0")
    # Close out
    await communicator.disconnect()
    assert "disconnected" in results


@pytest.mark.asyncio
async def test_async_websocket_consumer_subprotocol():
    """
    Tests that AsyncWebsocketConsumer correctly handles subprotocols.
    """

    class TestConsumer(AsyncWebsocketConsumer):
        async def connect(self):
            assert self.scope["subprotocols"] == ["subprotocol1", "subprotocol2"]
            await self.accept("subprotocol2")

    app = TestConsumer()

    # Test a normal connection with subprotocols
    communicator = WebsocketCommunicator(
        app, "/testws/", subprotocols=["subprotocol1", "subprotocol2"]
    )
    connected, subprotocol = await communicator.connect()
    assert connected
    assert subprotocol == "subprotocol2"


@pytest.mark.parametrize("channel_layer_kind", ["inmemory", "redis"])
@pytest.mark.asyncio
async def test_async_websocket_consumer_groups(channel_layer_kind, redis_layer):
    """
    Tests that AsyncWebsocketConsumer adds and removes channels from groups.
    """
    results = {}

    class TestConsumer(AsyncWebsocketConsumer):
        groups = ["chat"]
        channel_layer_alias = channel_layer_kind

        async def receive(self, text_data=None, bytes_data=None):
            results["received"] = (text_data, bytes_data)
            await self.send(text_data=text_data, bytes_data=bytes_data)

    app = TestConsumer()

    communicator = WebsocketCommunicator(app, "/testws/")
    await communicator.connect()

    channel_layer = get_channel_layer(channel_layer_kind)
    # Test that the websocket channel was added to the group on connect
    message = {"type": "websocket.receive", "text": "hello"}
    await channel_layer.group_send("chat", message)
    response = await communicator.receive_from()
    assert response == "hello"
    assert results["received"] == ("hello", None)

    # Test that the websocket channel was discarded from the group on disconnect
    await communicator.disconnect()
    if isinstance(channel_layer, InMemoryChannelLayer):
        assert channel_layer.groups == {}


@pytest.mark.asyncio
async def test_async_json_websocket_consumer():
    """
    Tests that AsyncJsonWebsocketConsumer is implemented correctly.
    """
    results = {}

    class TestConsumer(AsyncJsonWebsocketConsumer):
        async def connect(self):
            await self.accept()

        async def receive_json(self, content: Any, **kwargs: Any) -> None:
            results["received"] = content
            await self.send_json(content)

    app = TestConsumer()

    # Open a connection
    communicator = WebsocketCommunicator(app, "/testws/")
    connected, _ = await communicator.connect()
    assert connected
    # Test sending
    await communicator.send_json_to({"hello": "world"})
    response = await communicator.receive_json_from()
    assert response == {"hello": "world"}
    assert results["received"] == {"hello": "world"}
    # Test sending bytes breaks it
    await communicator.send_to(bytes_data=b"w\0\0\0")
    with pytest.raises(ValueError):
        await communicator.wait()


@pytest.mark.asyncio
async def test_block_underscored_type_function_call():
    """
    Test that consumer prevent calling private functions as handler
    """

    class TestConsumer(AsyncWebsocketConsumer):
        channel_layer_alias = "inmemory"

        async def _my_private_handler(self, _):
            await self.send(text_data="should never be called")

    app = TestConsumer()

    communicator = WebsocketCommunicator(app, "/testws/")
    await communicator.connect()

    channel_layer = get_channel_layer("inmemory")
    # Test that the specific channel layer is retrieved
    assert channel_layer is not None

    channel_name = list(channel_layer.channels.keys())[0]
    # Should block call to private functions handler and raise ValueError
    message = {"type": "_my_private_handler", "text": "hello"}
    await channel_layer.send(channel_name, message)
    with pytest.raises(
        ValueError, match=r"Malformed type in message \(leading underscore\)"
    ):
        await communicator.receive_from()


@pytest.mark.asyncio
async def test_block_leading_dot_type_function_call():
    """
    Test that consumer prevent calling private functions as handler
    """

    class TestConsumer(AsyncWebsocketConsumer):
        channel_layer_alias = "inmemory"

        async def _my_private_handler(self, _):
            await self.send(text_data="should never be called")

    app = TestConsumer()

    communicator = WebsocketCommunicator(app, "/testws/")
    await communicator.connect()

    channel_layer = get_channel_layer("inmemory")
    # Test that the specific channel layer is retrieved
    assert channel_layer is not None

    channel_name = list(channel_layer.channels.keys())[0]
    # Should not replace dot by underscore and call private function (see
    # issue: #1430)
    message = {"type": ".my_private_handler", "text": "hello"}
    await channel_layer.send(channel_name, message)
    with pytest.raises(
        ValueError, match=r"Malformed type in message \(leading underscore\)"
    ):
        await communicator.receive_from()


@pytest.mark.asyncio
async def test_accept_headers():
    """
    Tests that JsonWebsocketConsumer is implemented correctly.
    """

    class AsyncTestConsumer(AsyncWebsocketConsumer):
        async def connect(self):
            await self.accept(headers=[[b"foo", b"bar"]])

    app = AsyncTestConsumer()

    # Open a connection
    communicator = WebsocketCommunicator(app, "/testws/", spec_version="2.3")
    connected, _ = await communicator.connect()
    assert connected
    assert communicator.response_headers == [[b"foo", b"bar"]]


@pytest.mark.asyncio
async def test_close_reason():
    """
    Tests that JsonWebsocketConsumer is implemented correctly.
    """

    class AsyncTestConsumer(AsyncWebsocketConsumer):
        async def connect(self):
            await self.accept()
            await self.close(code=4007, reason="test reason")

    app = AsyncTestConsumer()

    # Open a connection
    communicator = WebsocketCommunicator(app, "/testws/", spec_version="2.3")
    connected, _ = await communicator.connect()
    msg = await communicator.receive_output()
    assert msg["type"] == "websocket.close"
    assert msg["code"] == 4007
    assert msg["reason"] == "test reason"


@pytest.mark.asyncio
async def test_websocket_receive_with_none_text():
    """
    Tests that the receive method handles messages with None text data correctly.
    """

    class TestConsumer(AsyncWebsocketConsumer):
        async def receive(self, text_data=None, bytes_data=None):
            if text_data:
                await self.send(text_data="Received text: " + text_data)
            elif bytes_data:
                await self.send(
                    text_data=f"Received bytes of length: {len(bytes_data)}"
                )

    app = TestConsumer()

    # Open a connection
    communicator = WebsocketCommunicator(app, "/testws/")
    connected, _ = await communicator.connect()
    assert connected

    # Simulate Hypercorn behavior
    # (both 'text' and 'bytes' keys present, but 'text' is None)
    await communicator.send_input(
        {
            "type": "websocket.receive",
            "text": None,
            "bytes": b"test data",
        }
    )
    response = await communicator.receive_output()
    assert response["type"] == "websocket.send"
    assert response["text"] == "Received bytes of length: 9"

    # Test with only 'bytes' key (simulating uvicorn/daphne behavior)
    await communicator.send_input({"type": "websocket.receive", "bytes": b"more data"})
    response = await communicator.receive_output()
    assert response["type"] == "websocket.send"
    assert response["text"] == "Received bytes of length: 9"

    # Test with valid text data
    await communicator.send_input(
        {"type": "websocket.receive", "text": "Hello, world!"}
    )
    response = await communicator.receive_output()
    assert response["type"] == "websocket.send"
    assert response["text"] == "Received text: Hello, world!"

    await communicator.disconnect()
