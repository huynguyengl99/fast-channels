#!/usr/bin/env python3
"""
Development startup script that runs both FastAPI app and RQ worker.

Usage:
    python sandbox/start_dev.py

This will start:
1. RQ worker in the background
2. FastAPI application with live reload

Both processes will be managed together and stopped with Ctrl+C.
"""

import signal
import subprocess
import sys
import time


def main():  # noqa
    """Start both worker and FastAPI app."""
    print("🚀 Starting development environment...")

    # Store process references
    worker_process = None
    app_process = None

    def cleanup(signum=None, frame=None):
        """Clean up processes on exit."""
        print("\n🛑 Shutting down...")

        if worker_process:
            print("🔄 Stopping RQ worker...")
            worker_process.terminate()
            try:
                worker_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                worker_process.kill()

        if app_process:
            print("🌐 Stopping FastAPI app...")
            app_process.terminate()
            try:
                app_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                app_process.kill()

        print("✅ Shutdown complete")
        sys.exit(0)

    # Set up signal handlers
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        # Start RQ worker
        print("🔄 Starting RQ worker...")
        worker_process = subprocess.Popen([sys.executable, "sandbox/worker.py"])

        # Give worker a moment to start
        time.sleep(2)

        # Start FastAPI app
        print("🌐 Starting FastAPI application...")
        app_process = subprocess.Popen(
            [
                "uvicorn",
                "sandbox.main:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8080",
                "--reload",
            ]
        )

        print("\n✅ Development environment ready!")
        print("📱 FastAPI app: http://localhost:8080")
        print("🔄 RQ worker: running in background")
        print("🛑 Press Ctrl+C to stop both services")

        # Wait for processes
        while True:
            # Check if either process has died
            if worker_process.poll() is not None:
                print("❌ RQ worker died unexpectedly")
                break
            if app_process.poll() is not None:
                print("❌ FastAPI app died unexpectedly")
                break

            time.sleep(1)

    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cleanup()


if __name__ == "__main__":
    main()
