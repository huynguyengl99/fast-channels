import asyncio
from urllib.parse import unquote

import pytest
from fast_channels.consumer import AsyncWebsocketConsumer
from fast_channels.testing import WebsocketCommunicator


class SimpleWebsocketApp(AsyncWebsocketConsumer):
    """
    Barebones WebSocket ASGI app for testing.
    """

    async def connect(self):
        assert self.scope["path"] == "/testws/"
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        await self.send(text_data=text_data, bytes_data=bytes_data)


class AcceptCloseWebsocketApp(AsyncWebsocketConsumer):
    async def connect(self):
        assert self.scope["path"] == "/testws/"
        await self.accept()
        await self.close()


class ErrorWebsocketApp(AsyncWebsocketConsumer):
    """
    Barebones WebSocket ASGI app for error testing.
    """

    async def receive(self, text_data=None, bytes_data=None):
        pass


class KwargsWebSocketApp(AsyncWebsocketConsumer):
    """
    WebSocket ASGI app used for testing the kwargs arguments in the url_route.
    """

    async def connect(self):
        await self.accept()
        await self.send(text_data=self.scope["url_route"]["kwargs"]["message"])


@pytest.mark.asyncio
async def test_websocket_communicator():
    """
    Tests that the WebSocket communicator class works at a basic level.
    """
    communicator = WebsocketCommunicator(SimpleWebsocketApp(), "/testws/")
    # Test connection
    connected, subprotocol = await communicator.connect()
    assert connected
    assert subprotocol is None
    # Test sending text
    await communicator.send_to(text_data="hello")
    response = await communicator.receive_from()
    assert response == "hello"
    # Test sending bytes
    await communicator.send_to(bytes_data=b"w\0\0\0")
    response = await communicator.receive_from()
    assert response == b"w\0\0\0"
    # Test sending JSON
    await communicator.send_json_to({"hello": "world"})
    response = await communicator.receive_json_from()
    assert response == {"hello": "world"}
    # Close out
    await communicator.disconnect()


@pytest.mark.asyncio
async def test_websocket_incorrect_read_json():
    """
    When using an invalid communicator method, an assertion error will be raised with
    informative message.
    In this test, the server accepts and then immediately closes the connection so
    the server is not in a valid state to handle "receive_from".
    """
    communicator = WebsocketCommunicator(AcceptCloseWebsocketApp(), "/testws/")
    await communicator.connect()
    with pytest.raises(AssertionError) as exception_info:
        await communicator.receive_from()
    assert (
        str(exception_info.value)
        == "Expected type 'websocket.send', but was 'websocket.close'"
    )


@pytest.mark.asyncio
async def test_timeout_disconnect():
    """
    Tests that communicator.disconnect() raises after a timeout. (Application
    is finished.)
    """
    communicator = WebsocketCommunicator(ErrorWebsocketApp(), "/testws/")
    # Test connection
    connected, subprotocol = await communicator.connect()
    assert connected
    assert subprotocol is None
    # Test sending text (will error internally)
    await communicator.send_to(text_data="hello")
    with pytest.raises(asyncio.TimeoutError):
        await communicator.receive_from()

    with pytest.raises(asyncio.exceptions.CancelledError):
        await communicator.disconnect()


class ConnectionScopeValidator(AsyncWebsocketConsumer):
    """
    Tests ASGI specification for the connection scope.
    """

    async def connect(self):
        assert self.scope["type"] == "websocket"
        # check if path is a unicode string
        assert isinstance(self.scope["path"], str)
        # check if path has percent escapes decoded
        assert self.scope["path"] == unquote(self.scope["path"])
        # check if query_string is a bytes sequence
        assert isinstance(self.scope["query_string"], bytes)
        await self.accept()


paths = [
    "user:pass@example.com:8080/p/a/t/h?query=string#hash",
    "wss://user:pass@example.com:8080/p/a/t/h?query=string#hash",
    (
        "ws://www.example.com/%E9%A6%96%E9%A1%B5/index.php?"
        "foo=%E9%A6%96%E9%A1%B5&spam=eggs"
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("path", paths)
async def test_connection_scope(path):
    """
    Tests ASGI specification for the the connection scope.
    """
    communicator = WebsocketCommunicator(ConnectionScopeValidator(), path)
    connected, _ = await communicator.connect()
    assert connected
    await communicator.disconnect()
