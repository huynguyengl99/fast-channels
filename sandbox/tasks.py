"""
Background tasks for the sandbox application.
"""

import time
from typing import Any

from asgiref.sync import async_to_sync
from fast_channels.layers import get_channel_layer
from redis import Redis
from rq import Queue

from sandbox.layers import setup_layers

# Setup channel layers when this module is imported
setup_layers()

# Redis connection for RQ
redis_conn = Redis(host="localhost", port=6399, db=1)  # Use different DB than channels
job_queue = Queue("background_jobs", connection=redis_conn)


def translate_text(job_id: str, content: str, channel_name: str) -> dict[str, Any]:
    """
    Simulate text translation task.
    """
    time.sleep(2)  # Simulate API call delay

    # Simple mock translation
    translations = {
        "hello": "hola",
        "world": "mundo",
        "good morning": "buenos días",
        "thank you": "gracias",
    }

    translated = translations.get(content.lower(), f"[TRANSLATED: {content}]")
    result = f"🌍 Translated: '{content}' → '{translated}'"

    # Send result back through channel layer
    _send_result_to_client(channel_name, result)

    return {"status": "completed", "result": result, "job_id": job_id}


def analyze_text(job_id: str, content: str, channel_name: str) -> dict[str, Any]:
    """
    Simulate text analysis task.
    """
    time.sleep(3)  # Simulate processing delay

    # Perform analysis
    word_count = len(content.split())
    char_count = len(content)
    vowel_count = sum(1 for char in content.lower() if char in "aeiou")
    consonant_count = sum(
        1 for char in content.lower() if char.isalpha() and char not in "aeiou"
    )

    result = (
        f"📊 Analysis of '{content}':\n"
        f"• Characters: {char_count}\n"
        f"• Words: {word_count}\n"
        f"• Vowels: {vowel_count}\n"
        f"• Consonants: {consonant_count}"
    )

    # Send result back through channel layer
    _send_result_to_client(channel_name, result)

    return {"status": "completed", "result": result, "job_id": job_id}


def generate_response(job_id: str, content: str, channel_name: str) -> dict[str, Any]:
    """
    Simulate AI response generation.
    """
    time.sleep(4)  # Simulate AI processing

    # Simple response generation based on keywords
    if "weather" in content.lower():
        response = "The weather is looking great today! Perfect for a walk outside."
    elif "food" in content.lower() or "eat" in content.lower():
        response = "I'd recommend trying that new restaurant downtown. Their pasta is excellent!"
    elif "help" in content.lower():
        response = "I'm here to help! Feel free to ask me anything you'd like to know."
    else:
        response = f"That's an interesting point about '{content}'. Let me think about that... Based on my analysis, I would suggest exploring this topic further through research and practical application."

    result = f"🤖 AI Response to '{content}':\n{response}"

    # Send result back through channel layer
    _send_result_to_client(channel_name, result)

    return {"status": "completed", "result": result, "job_id": job_id}


def process_default(job_id: str, content: str, channel_name: str) -> dict[str, Any]:
    """
    Default processing task.
    """
    time.sleep(1)  # Quick processing

    result = f"✅ Processed: {content.upper()}"

    # Send result back through channel layer
    _send_result_to_client(channel_name, result)

    return {"status": "completed", "result": result, "job_id": job_id}


def _send_result_to_client(channel_name: str, message: str) -> None:
    """
    Send the result back to the WebSocket client through the channel layer.
    """
    try:
        # Get the chat channel layer (same as used by BackgroundJobConsumer)
        channel_layer = get_channel_layer("chat")
        assert channel_layer

        # Use asgiref to convert async call to sync
        async_to_sync(channel_layer.send)(
            channel_name, {"type": "job_result", "message": message}
        )

    except Exception as e:
        print(f"Error sending result to client: {e}")


# Job dispatcher
JOB_FUNCTIONS = {
    "translate": translate_text,
    "analyze": analyze_text,
    "generate": generate_response,
    "default": process_default,
}


def queue_job(job_type: str, content: str, channel_name: str) -> str:
    """
    Queue a background job and return the job ID.
    """
    if job_type not in JOB_FUNCTIONS:
        job_type = "default"

    job_func = JOB_FUNCTIONS[job_type]
    job = job_queue.enqueue(  # type: ignore[misc]
        job_func, job_type + "_" + str(int(time.time())), content, channel_name
    )

    return job.id
