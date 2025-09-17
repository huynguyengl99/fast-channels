"""
System Chat Consumer Template

This template shows how to create a simple WebSocket consumer without channel layers.
Perfect for direct client-server communication.

TODO:
1. Customize the connect() method with your welcome message
2. Add your own message processing logic in receive()
3. Handle disconnections if needed
"""

from fast_channels.consumer.websocket import AsyncWebsocketConsumer


class SystemMessageConsumer(AsyncWebsocketConsumer):
    """
    Consumer for system messages without using channel layers.
    Direct connection without group messaging.
    """

    async def connect(self):
        await self.accept()
        # TODO: Customize your welcome message
        await self.send("🔧 System: Connection established!")

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        # TODO: Add your message processing logic here
        # Example: Echo back system message directly without using layers
        await self.send(f"🔧 System Echo: {text_data}")

    async def disconnect(self, close_code):
        # TODO: Add any cleanup logic here if needed
        pass
