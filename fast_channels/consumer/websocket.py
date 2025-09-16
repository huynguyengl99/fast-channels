import json
from typing import Any

from ..exceptions import (
    AcceptConnection,
    DenyConnection,
    InvalidChannelLayerError,
    StopConsumer,
)
from ..types import (
    ChannelHeaders,
    WebSocketAcceptEvent,
    WebSocketCloseEvent,
    WebSocketConnectEvent,
    WebSocketDisconnectEvent,
    WebSocketReceiveEvent,
)
from .base import AsyncConsumer


class AsyncWebsocketConsumer(AsyncConsumer):
    """
    Base WebSocket consumer, async version. Provides a general encapsulation
    for the WebSocket handling model that other applications can build on.
    """

    groups: list[str]

    def __init__(self, *args, **kwargs):
        if not getattr(self, "groups", None):
            self.groups = []

    async def websocket_connect(self, message: WebSocketConnectEvent) -> None:
        """
        Called when a WebSocket connection is opened.
        """
        try:
            for group in self.groups:
                await self.channel_layer.group_add(group, self.channel_name)
        except AttributeError:
            raise InvalidChannelLayerError(
                "BACKEND is unconfigured or doesn't support groups"
            ) from None
        try:
            await self.connect()
        except AcceptConnection:
            await self.accept()
        except DenyConnection:
            await self.close()

    async def connect(self) -> None:
        await self.accept()

    async def accept(
        self, subprotocol: str | None = None, headers: ChannelHeaders | None = None
    ):
        """
        Accepts an incoming socket
        """
        message: WebSocketAcceptEvent = {
            "type": "websocket.accept",
            "subprotocol": subprotocol,
            "headers": list(headers) if headers else [],
        }
        await super().send(message)

    async def websocket_receive(self, message: WebSocketReceiveEvent):
        """
        Called when a WebSocket frame is received. Decodes it and passes it
        to receive().
        """
        if message.get("text") is not None:
            await self.receive(text_data=message["text"])
        else:
            await self.receive(bytes_data=message["bytes"])

    async def receive(
        self, text_data: str | None = None, bytes_data: bytes | None = None
    ) -> None:
        """
        Called with a decoded WebSocket frame.
        """
        pass

    async def send(
        self,
        text_data: str | None = None,
        bytes_data: bytes | None = None,
        close: bool = False,
    ) -> None:
        """
        Sends a reply back down the WebSocket
        """
        if text_data is not None:
            await super().send({"type": "websocket.send", "text": text_data})
        elif bytes_data is not None:
            await super().send({"type": "websocket.send", "bytes": bytes_data})
        else:
            raise ValueError("You must pass one of bytes_data or text_data")
        if close:
            await self.close(close)

    async def close(
        self, code: int | bool | None = None, reason: str | None = None
    ) -> None:
        """
        Closes the WebSocket from the server end
        """
        message: WebSocketCloseEvent = {
            "type": "websocket.close",
            "code": code if isinstance(code, int) else 1000,
            "reason": reason,
        }

        await super().send(message)

    async def websocket_disconnect(self, message: WebSocketDisconnectEvent) -> None:
        """
        Called when a WebSocket connection is closed. Base level so you don't
        need to call super() all the time.
        """
        try:
            for group in self.groups:
                await self.channel_layer.group_discard(group, self.channel_name)
        except AttributeError:
            raise InvalidChannelLayerError(
                "BACKEND is unconfigured or doesn't support groups"
            ) from None
        await self.disconnect(message["code"])
        raise StopConsumer()

    async def disconnect(self, code: int) -> None:
        """
        Called when a WebSocket connection is closed.
        """
        pass


class AsyncJsonWebsocketConsumer(AsyncWebsocketConsumer):
    """
    Variant of AsyncWebsocketConsumer that automatically JSON-encodes and decodes
    messages as they come in and go out. Expects everything to be text; will
    error on binary data.
    """

    async def receive(
        self,
        text_data: str | None = None,
        bytes_data: bytes | None = None,
        **kwargs: Any,
    ) -> None:
        if text_data:
            await self.receive_json(await self.decode_json(text_data), **kwargs)
        else:
            raise ValueError("No text section for incoming WebSocket frame!")

    async def receive_json(self, content: Any, **kwargs: Any) -> None:
        """
        Called with decoded JSON content.
        """
        pass

    async def send_json(self, content: Any, close: bool = False) -> None:
        """
        Encode the given content as JSON and send it to the client.
        """
        await super().send(text_data=await self.encode_json(content), close=close)

    @classmethod
    async def decode_json(cls, text_data: str) -> Any:
        return json.loads(text_data)

    @classmethod
    async def encode_json(cls, content: Any) -> str:
        return json.dumps(content)
