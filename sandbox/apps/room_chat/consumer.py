"""
Room Chat Consumer - Dynamic room-based messaging.
"""

from typing import Any

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
        assert self.channel_layer
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # Send join notification to the room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "room_message",
                "message": f"🚪 Someone joined room '{self.room_name}'",
            },
        )

    async def disconnect(self, code: int) -> None:
        # Leave room group
        assert self.channel_layer
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        # Send leave notification to the room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "room_message",
                "message": f"👋 Someone left room '{self.room_name}'",
            },
        )

    async def receive(
        self,
        text_data: str | None = None,
        bytes_data: bytes | None = None,
        **kwargs: Any,
    ) -> None:
        # Send message to room group
        assert self.channel_layer
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "room_message", "message": f"💬 {text_data}"}
        )

    async def room_message(self, event: dict[str, Any]) -> None:
        """
        Called when someone has messaged our room.
        """
        await self.send(event["message"])
