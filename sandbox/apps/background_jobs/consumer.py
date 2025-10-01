"""
Background Jobs Consumer - Real background job processing with RQ.
"""

from typing import Any, cast

from fast_channels.consumer.websocket import AsyncJsonWebsocketConsumer

from sandbox.tasks import queue_job


class BackgroundJobConsumer(AsyncJsonWebsocketConsumer):
    """
    Consumer for processing messages with real background jobs using RQ.
    """

    channel_layer_alias = "chat"

    async def connect(self):
        await self.accept()
        await self.send_json(
            {
                "status": "connected",
                "message": "🔄 Background Job Processor: Connected!",
            }
        )

    async def receive_json(self, content: dict[str, Any], **kwargs: Any) -> None:
        try:
            # Extract job type and content from JSON
            job_type = content.get("type", "default")
            job_content = cast(str, content.get("content"))

            # Show immediate response that job is being queued
            await self.send_json(
                {
                    "status": "queuing",
                    "message": f"⏳ Queuing {job_type} job: {job_content}",
                }
            )

            # Queue the real background job
            job_id = queue_job(job_type, job_content, self.channel_name)

            await self.send_json(
                {
                    "status": "queued",
                    "job_id": job_id,
                    "message": (
                        f"📋 Job {job_id} queued successfully! Worker will process it shortly..."
                    ),
                }
            )

        except Exception as e:
            await self.send_json(
                {"status": "error", "message": f"❌ Error queuing job: {str(e)}"}
            )

    async def job_result(self, event: dict[str, Any]) -> None:
        """
        Handle job results sent back from background workers.
        """
        await self.send_json({"type": "job_result", "message": event["message"]})

    async def disconnect(self, code: int) -> None:
        pass
