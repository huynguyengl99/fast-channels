"""
Background Jobs Consumer Template

This template shows how to integrate WebSocket consumers with background job processing.
Demonstrates real async job queuing and result delivery.

TODO:
1. Create your tasks.py file with job functions
2. Configure your job queue system (RQ, Celery, etc.)
3. Customize job types and processing logic
"""

import json

from fast_channels.consumer.websocket import AsyncWebsocketConsumer
from sandbox.tasks import queue_job


class BackgroundJobConsumer(AsyncWebsocketConsumer):
    """
    Consumer for processing messages with real background jobs.
    """

    # TODO: Configure your channel layer alias
    channel_layer_alias = "chat"

    async def connect(self):
        await self.accept()
        # TODO: Customize your welcome message
        await self.send("🔄 Background Job Processor: Connected!")

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        try:
            # Parse message if it's JSON, otherwise treat as plain text
            try:
                data = json.loads(text_data)
                job_type = data.get("type", "default")
                content = data.get("content", text_data)
            except (json.JSONDecodeError, AttributeError):
                job_type = "default"
                content = text_data

            # TODO: Customize your job queuing logic
            await self.send(f"⏳ Queuing {job_type} job: {content}")

            job_id = queue_job(job_type, content, self.channel_name)
            await self.send(f"📋 Job {job_id} queued successfully!")

        except Exception as e:
            await self.send(f"❌ Error queuing job: {str(e)}")

    async def job_result(self, event):
        """
        Handle job results sent back from background workers.
        TODO: Customize result processing if needed
        """
        await self.send(event["message"])

    async def disconnect(self, close_code):
        # TODO: Add cleanup logic if needed
        pass
