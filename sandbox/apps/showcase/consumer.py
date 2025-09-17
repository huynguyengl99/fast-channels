"""
Layers Combo Consumers - Different channel layer types working together.
"""

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
        await self.channel_layer.group_send(
            "chat_room",
            {"type": "chat_message", "message": "📢 Someone joined the chat"},
        )

    async def disconnect(self, code):
        """Handle WebSocket disconnection for chat."""
        await super().disconnect(code)
        await self.channel_layer.group_send(
            "chat_room",
            {"type": "chat_message", "message": "❌ Someone left the chat."},
        )

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        """Handle incoming WebSocket messages for chat."""
        await self.channel_layer.group_send(
            "chat_room", {"type": "chat_message", "message": f"💬 {text_data}"}
        )

    async def chat_message(self, event):
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Use the pre-configured queue layer (Redis queue-based)

    async def connect(self):
        await self.accept()
        await self.channel_layer.group_send(
            "reliable_chat",
            {
                "type": "reliable_chat_message",
                "message": "🔒 Reliable chat connection established!",
            },
        )

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        await self.channel_layer.group_send(
            "reliable_chat",
            {"type": "reliable_chat_message", "message": f"📨 {text_data}"},
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_send(
            "reliable_chat",
            {"type": "reliable_chat_message", "message": "🚪 Left reliable chat!"},
        )

    async def reliable_chat_message(self, event):
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
        await self.channel_layer.group_send(
            "notifications",
            {
                "type": "notification_message",
                "data": {"type": "system", "message": "🔔 Connected to notifications!"},
            },
        )

    async def receive_json(self, content, **kwargs):
        # Echo notification back to all connected clients
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

    async def disconnect(self, close_code):
        pass  # No disconnect message for notifications

    async def notification_message(self, event):
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

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        # Process analytics event
        await self.channel_layer.group_send(
            "analytics",
            {"type": "analytics_message", "message": f"📊 Analytics: {text_data}"},
        )

    async def disconnect(self, close_code):
        pass

    async def analytics_message(self, event):
        """
        Called when an analytics event is sent to the group.
        """
        await self.send(event["message"])
