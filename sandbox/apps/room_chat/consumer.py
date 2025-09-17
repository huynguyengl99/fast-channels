"""
Room Chat Consumer - Dynamic room-based messaging.
"""

from fast_channels.consumer.websocket import AsyncWebsocketConsumer


class RoomChatConsumer(AsyncWebsocketConsumer):
    """
    Consumer for room-based chat where users can join specific rooms.
    """

    channel_layer_alias = "chat"

    async def connect(self):
        # Extract room name from path parameters
        self.room_name = self.scope["path_params"]["room_name"]
        self.room_group_name = f"room_{self.room_name}"

        await self.accept()

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # Send join notification to the room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "room_message",
                "message": f"🚪 Someone joined room '{self.room_name}'",
            },
        )

    async def disconnect(self, code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        # Send leave notification to the room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "room_message",
                "message": f"👋 Someone left room '{self.room_name}'",
            },
        )

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "room_message", "message": f"💬 {text_data}"}
        )

    async def room_message(self, event):
        """
        Called when someone has messaged our room.
        """
        await self.send(event["message"])
