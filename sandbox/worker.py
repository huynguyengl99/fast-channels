#!/usr/bin/env python3
"""
RQ Worker for processing background jobs.

Usage:
    python sandbox/worker.py

This script starts an RQ worker that will process jobs from the 'background_jobs' queue.
Run this alongside your FastAPI application to handle background job processing.
"""

import os
import signal
import sys

# Add the project root to Python path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # noqa

from redis import Redis
from rq import Queue, Worker

from sandbox.layers import setup_layers


def main():
    """Start the RQ worker."""
    print("🔧 Setting up channel layers...")
    setup_layers()

    print("🔗 Connecting to Redis...")
    # Use same Redis settings as in tasks.py
    redis_conn = Redis(host="localhost", port=6399, db=1)

    # Test Redis connection
    try:
        redis_conn.ping()
        print("✅ Redis connection successful!")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("Make sure Redis is running on localhost:6399")
        sys.exit(1)

    # Create queue
    queue = Queue("background_jobs", connection=redis_conn)

    print(f"🚀 Starting RQ worker for queue: {queue.name}")
    print("📋 Jobs will be processed as they arrive...")
    print("🛑 Press Ctrl+C to stop the worker")

    # Create worker
    worker = Worker([queue], connection=redis_conn)

    # Handle graceful shutdown
    def signal_handler(sig, frame):
        print("\n🛑 Shutting down worker gracefully...")
        worker.request_stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start working
    try:
        worker.work(with_scheduler=True)
    except KeyboardInterrupt:
        print("\n🛑 Worker stopped by user")
    except Exception as e:
        print(f"❌ Worker error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
