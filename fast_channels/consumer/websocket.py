"""WebSocket consumer implementations for the fast-channels framework.

This module provides base WebSocket consumer classes for handling WebSocket
connections with support for JSON message handling and group management.
"""

import json
from typing import Any

from fast_channels.exceptions import (
    AcceptConnection,
    DenyConnection,
    InvalidChannelLayerError,
    StopConsumer,
)
from fast_channels.type_defs import (
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

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the WebSocket consumer.

        Args:
            *args: Positional arguments.
            **kwargs: Keyword arguments.
        """
        if not getattr(self, "groups", None):
            self.groups = []

    async def websocket_connect(self, message: WebSocketConnectEvent) -> None:
        """
        Called when a WebSocket connection is opened.

        Args:
            message: WebSocket connect event containing connection details.
        """
        try:
            for group in self.groups:
                if self.channel_layer:
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
        """Handle WebSocket connection establishment.

        Override this method to customize connection handling.
        By default, automatically accepts the connection.
        """
        await self.accept()

    async def accept(
        self, subprotocol: str | None = None, headers: ChannelHeaders | None = None
    ) -> None:
        """
        Accepts an incoming socket

        Args:
            subprotocol: Optional WebSocket subprotocol to use.
            headers: Optional headers to send with the accept message.
        """
        message: WebSocketAcceptEvent = {
            "type": "websocket.accept",
            "subprotocol": subprotocol,
            "headers": list(headers) if headers else [],
        }
        await super().send(message)

    async def websocket_receive(self, message: WebSocketReceiveEvent) -> None:
        """
        Called when a WebSocket frame is received. Decodes it and passes it
        to receive().

        Args:
            message: WebSocket receive event containing the frame data.
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

        Args:
            text_data: Text data from the WebSocket frame, if any.
            bytes_data: Binary data from the WebSocket frame, if any.
        """
        pass

    async def send(  # type: ignore[override]
        self,
        text_data: str | None = None,
        bytes_data: bytes | None = None,
        close: bool = False,
    ) -> None:
        """
        Sends a reply back down the WebSocket

        Args:
            text_data: Text data to send, if any.
            bytes_data: Binary data to send, if any.
            close: Whether to close the connection after sending.

        Raises:
            ValueError: If neither text_data nor bytes_data is provided.
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

        Args:
            code: Close code (defaults to 1000) or boolean for legacy support.
            reason: Optional reason for closing the connection.
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

        Args:
            message: WebSocket disconnect event containing disconnect details.
        """
        try:
            for group in self.groups:
                if self.channel_layer:
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

        Args:
            code: The WebSocket close code.
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
        """Handle incoming WebSocket frames and decode JSON content.

        Args:
            text_data: Text data from the WebSocket frame.
            bytes_data: Bytes data from the WebSocket frame (not supported).
            **kwargs: Additional keyword arguments.

        Raises:
            ValueError: If no text data is provided or bytes data is received.
        """
        if text_data:
            await self.receive_json(await self.decode_json(text_data), **kwargs)
        else:
            raise ValueError("No text section for incoming WebSocket frame!")

    async def receive_json(self, content: Any, **kwargs: Any) -> None:
        """
        Called with decoded JSON content.

        Args:
            content: The decoded JSON content.
            **kwargs: Additional keyword arguments.
        """
        pass

    async def send_json(self, content: Any, close: bool = False) -> None:
        """
        Encode the given content as JSON and send it to the client.

        Args:
            content: The content to encode and send as JSON.
            close: Whether to close the connection after sending.
        """
        await super().send(text_data=await self.encode_json(content), close=close)

    @classmethod
    async def decode_json(cls, text_data: str) -> Any:
        """Decode JSON from text data.

        Args:
            text_data: JSON string to decode.

        Returns:
            The decoded JSON object.
        """
        return json.loads(text_data)

    @classmethod
    async def encode_json(cls, content: Any) -> str:
        """Encode content as JSON string.

        Args:
            content: Object to encode as JSON.

        Returns:
            JSON string representation.
        """
        return json.dumps(content)
