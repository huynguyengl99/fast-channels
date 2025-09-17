"""
System Chat Consumer - Direct WebSocket without channel layers.
"""

from fast_channels.consumer.websocket import AsyncWebsocketConsumer


class SystemMessageConsumer(AsyncWebsocketConsumer):
    """
    Consumer for system messages without using channel layers.
    Direct connection without group messaging.
    """

    async def connect(self):
        await self.accept()
        await self.send("🔧 System: Connection established!")

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        # Echo back system message directly without using layers
        await self.send(f"🔧 System Echo: {text_data}")

    async def disconnect(self, close_code):
        pass
