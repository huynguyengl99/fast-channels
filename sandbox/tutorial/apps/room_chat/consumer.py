"""
Room Chat Consumer Template

This template demonstrates channel layers with dynamic room groups.
Users can join specific rooms and chat with others in the same room.

TODO:
1. Customize room group naming if needed
2. Add custom join/leave messages
3. Implement room-specific logic (permissions, etc.)
"""

from typing import Any

from fast_channels.consumer.websocket import AsyncWebsocketConsumer


class RoomChatConsumer(AsyncWebsocketConsumer):
    """
    Consumer for room-based chat where users can join specific rooms.
    """

    # TODO: Configure your channel layer alias
    channel_layer_alias = "chat"

    async def connect(self):
        # Extract room name from path parameters
        assert self.channel_layer
        self.room_name = self.scope["path_params"]["room_name"]
        self.room_group_name = f"room_{self.room_name}"

        await self.accept()

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # TODO: Customize your join message
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

        # TODO: Customize your leave message
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
        assert self.channel_layer
        # TODO: Add message processing/filtering logic here
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "room_message", "message": f"💬 {text_data}"}
        )

    async def room_message(self, event: dict[str, Any]) -> None:
        """
        Called when someone has messaged our room.
        """
        # TODO: Add message formatting/filtering here if needed
        await self.send(event["message"])
