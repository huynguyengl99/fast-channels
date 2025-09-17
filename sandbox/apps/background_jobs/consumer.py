"""
Background Jobs Consumer - Real background job processing with RQ.
"""

import json

from fast_channels.consumer.websocket import AsyncWebsocketConsumer

from sandbox.tasks import queue_job


class BackgroundJobConsumer(AsyncWebsocketConsumer):
    """
    Consumer for processing messages with real background jobs using RQ.
    """

    channel_layer_alias = "chat"

    async def connect(self):
        await self.accept()
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

            # Show immediate response that job is being queued
            await self.send(f"⏳ Queuing {job_type} job: {content}")

            # Queue the real background job
            job_id = queue_job(job_type, content, self.channel_name)

            await self.send(
                f"📋 Job {job_id} queued successfully! Worker will process it shortly..."
            )

        except Exception as e:
            await self.send(f"❌ Error queuing job: {str(e)}")

    async def job_result(self, event):
        """
        Handle job results sent back from background workers.
        """
        await self.send(event["message"])

    async def disconnect(self, close_code):
        pass
