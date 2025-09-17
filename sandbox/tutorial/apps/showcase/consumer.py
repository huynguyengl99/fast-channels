"""
Showcase Consumers Template

This template demonstrates multiple channel layer types working together.
Shows different layer configurations and use cases.

TODO:
1. Configure your channel layer aliases in layers.py
2. Customize group names and message types
3. Add your own consumer types as needed
"""

from fast_channels.consumer.websocket import (
    AsyncJsonWebsocketConsumer,
    AsyncWebsocketConsumer,
)


class ChatConsumer(AsyncWebsocketConsumer):
    """
    Basic chat consumer using the centralized chat layer.
    """

    groups = ["chat_room"]
    channel_layer_alias = "chat"  # TODO: Configure in your layers.py

    async def connect(self):
        await self.accept()
        # TODO: Customize join message
        await self.channel_layer.group_send(
            "chat_room",
            {"type": "chat_message", "message": "📢 Someone joined the chat"},
        )

    async def disconnect(self, code):
        await super().disconnect(code)
        # TODO: Customize leave message
        await self.channel_layer.group_send(
            "chat_room",
            {"type": "chat_message", "message": "❌ Someone left the chat."},
        )

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        # TODO: Add message processing logic
        await self.channel_layer.group_send(
            "chat_room", {"type": "chat_message", "message": f"💬 {text_data}"}
        )

    async def chat_message(self, event):
        """Called when someone has messaged our chat."""
        await self.send(event["message"])


class ReliableChatConsumer(AsyncWebsocketConsumer):
    """
    Chat consumer using queue-based layer for guaranteed message delivery.
    """

    channel_layer_alias = "queue"  # TODO: Configure in your layers.py
    groups = ["reliable_chat"]

    async def connect(self):
        await self.accept()
        # TODO: Customize connection message
        await self.channel_layer.group_send(
            "reliable_chat",
            {
                "type": "reliable_chat_message",
                "message": "🔒 Reliable chat connection established!",
            },
        )

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        # TODO: Add reliable message processing
        await self.channel_layer.group_send(
            "reliable_chat",
            {"type": "reliable_chat_message", "message": f"📨 {text_data}"},
        )

    async def disconnect(self, close_code):
        # TODO: Add disconnect handling
        await self.channel_layer.group_send(
            "reliable_chat",
            {"type": "reliable_chat_message", "message": "🚪 Left reliable chat!"},
        )

    async def reliable_chat_message(self, event):
        """Called when someone has messaged our reliable chat."""
        await self.send(event["message"])


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """
    Consumer for real-time notifications using JSON messages.
    """

    channel_layer_alias = "notifications"  # TODO: Configure in your layers.py
    groups = ["notifications"]

    async def connect(self):
        await self.accept()
        # TODO: Customize notification connection message
        await self.channel_layer.group_send(
            "notifications",
            {
                "type": "notification_message",
                "data": {"type": "system", "message": "🔔 Connected to notifications!"},
            },
        )

    async def receive_json(self, content, **kwargs):
        # TODO: Add JSON notification processing logic
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
        # TODO: Add notification disconnect handling if needed
        pass

    async def notification_message(self, event):
        """Called when a notification is sent to the group."""
        await self.send_json(event["data"])


# TODO: Implement the AnalyticsConsumer class below
# Hints:
# 1. Use channel_layer_alias = "analytics"
# 2. Use groups = ["analytics"]
# 3. Create analytics_message method to handle events
# 4. Consider JSON message format for structured analytics data
# 5. Process analytics events and send them to the group
# 6. Handle connection/disconnection as needed for your use case


class AnalyticsConsumer(AsyncWebsocketConsumer):
    """
    TODO: Consumer for analytics events with reliable delivery.

    Implement this consumer by:
    1. Setting up the proper channel layer alias and groups
    2. Handling connection, receive, and disconnect methods
    3. Creating an analytics_message method for group events
    4. Processing analytics events appropriately
    """

    # TODO: Add your implementation here
    pass
