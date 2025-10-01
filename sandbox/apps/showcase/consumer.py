"""
Layers Combo Consumers - Different channel layer types working together.
"""

from typing import Any

from fast_channels.consumer.websocket import (
    AsyncJsonWebsocketConsumer,
    AsyncWebsocketConsumer,
)


class ChatConsumer(AsyncWebsocketConsumer):
    """
    Chat consumer using the centralized chat layer.
    """

    groups = ["chat_room"]
    channel_layer_alias = "chat"

    async def connect(self):
        """Handle WebSocket connection for chat."""
        await self.accept()
        assert self.channel_layer
        await self.channel_layer.group_send(
            "chat_room",
            {"type": "chat_message", "message": "📢 Someone joined the chat"},
        )

    async def disconnect(self, code: int) -> None:
        """Handle WebSocket disconnection for chat."""
        await super().disconnect(code)
        assert self.channel_layer
        await self.channel_layer.group_send(
            "chat_room",
            {"type": "chat_message", "message": "❌ Someone left the chat."},
        )

    async def receive(
        self,
        text_data: str | None = None,
        bytes_data: bytes | None = None,
        **kwargs: Any,
    ) -> None:
        """Handle incoming WebSocket messages for chat."""
        assert self.channel_layer
        await self.channel_layer.group_send(
            "chat_room", {"type": "chat_message", "message": f"💬 {text_data}"}
        )

    async def chat_message(self, event: dict[str, Any]) -> None:
        """
        Called when someone has messaged our chat.
        """
        # Send a message down to the client
        await self.send(event["message"])


class ReliableChatConsumer(AsyncWebsocketConsumer):
    """
    Chat consumer using the queue-based layer for guaranteed message delivery.
    """

    channel_layer_alias = "queue"
    groups = ["reliable_chat"]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Use the pre-configured queue layer (Redis queue-based)

    async def connect(self):
        await self.accept()
        assert self.channel_layer
        await self.channel_layer.group_send(
            "reliable_chat",
            {
                "type": "reliable_chat_message",
                "message": "🔒 Reliable chat connection established!",
            },
        )

    async def receive(
        self,
        text_data: str | None = None,
        bytes_data: bytes | None = None,
        **kwargs: Any,
    ) -> None:
        assert self.channel_layer
        await self.channel_layer.group_send(
            "reliable_chat",
            {"type": "reliable_chat_message", "message": f"📨 {text_data}"},
        )

    async def disconnect(self, code: int) -> None:
        assert self.channel_layer
        await self.channel_layer.group_send(
            "reliable_chat",
            {"type": "reliable_chat_message", "message": "🚪 Left reliable chat!"},
        )

    async def reliable_chat_message(self, event: dict[str, Any]) -> None:
        """
        Called when someone has messaged our reliable chat.
        """
        await self.send(event["message"])


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """
    Consumer for real-time notifications using JSON messages.
    """

    channel_layer_alias = "notifications"
    groups = ["notifications"]

    async def connect(self):
        await self.accept()
        assert self.channel_layer
        await self.channel_layer.group_send(
            "notifications",
            {
                "type": "notification_message",
                "data": {"type": "system", "message": "🔔 Connected to notifications!"},
            },
        )

    async def receive_json(self, content: Any, **kwargs: Any) -> None:
        # Echo notification back to all connected clients
        assert self.channel_layer
        await self.channel_layer.group_send(
            "notifications",
            {
                "type": "notification_message",
                "data": {
                    "type": "user",
                    "message": (
                        f"🔔 Notification: {content.get('message', 'No message')}"
                    ),
                },
            },
        )

    async def disconnect(self, code: int) -> None:
        pass  # No disconnect message for notifications

    async def notification_message(self, event: dict[str, Any]) -> None:
        """
        Called when a notification is sent to the group.
        """
        await self.send_json(event["data"])


class AnalyticsConsumer(AsyncWebsocketConsumer):
    """
    Consumer for analytics events with reliable delivery.
    """

    channel_layer_alias = "analytics"
    groups = ["analytics"]

    async def connect(self):
        await self.accept()

    async def receive(
        self,
        text_data: str | None = None,
        bytes_data: bytes | None = None,
        **kwargs: Any,
    ) -> None:
        # Process analytics event
        assert self.channel_layer
        await self.channel_layer.group_send(
            "analytics",
            {"type": "analytics_message", "message": f"📊 Analytics: {text_data}"},
        )

    async def disconnect(self, code: int) -> None:
        pass

    async def analytics_message(self, event: dict[str, Any]) -> None:
        """
        Called when an analytics event is sent to the group.
        """
        await self.send(event["message"])
