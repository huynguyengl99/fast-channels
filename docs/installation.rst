Installation
============

Fast Channels can be installed via pip and supports Python 3.11+.

Requirements
------------

- **Python 3.11+** - Fast Channels requires Python 3.11 or higher
- **ASGI Framework** - FastAPI, Starlette, Quart, or any ASGI-compatible framework
- **Redis** (optional) - For production channel layers with cross-process communication

Basic Installation
------------------

Install Fast Channels using pip:

.. code-block:: bash

    pip install fast-channels

This installs the core Fast Channels package with in-memory channel layer support, suitable for development and testing.

Recommended Installation
------------------------

For production use, install with Redis support:

.. code-block:: bash

    pip install "fast-channels[redis]"

This includes Redis-backed channel layers for reliable, scalable real-time communication across multiple processes.

Optional Dependencies
---------------------

**Redis Support:**

.. code-block:: bash

    pip install "fast-channels[redis]"

Includes Redis channel layer backends for production use. This is the only optional dependency available.

Setting Up Redis (Production)
-----------------------------

For production deployments, you'll need a Redis server for channel layers:

**Using Docker:**

.. code-block:: bash

    # Run Redis in Docker
    docker run -d -p 6379:6379 redis:alpine

**Using Docker Compose:**

.. code-block:: yaml

    # docker-compose.yml
    version: '3.8'
    services:
      redis:
        image: redis:alpine
        ports:
          - "6379:6379"

**System Installation:**

.. code-block:: bash

    # Ubuntu/Debian
    sudo apt update && sudo apt install redis-server

    # macOS with Homebrew
    brew install redis

    # Start Redis
    redis-server

Troubleshooting
---------------

**Import Error:**
   Make sure you're using Python 3.11+ and Fast Channels is installed in the correct environment.

**Redis Connection Error:**
   Verify Redis is running and accessible at the specified URL. Check firewall settings and Redis configuration.

Next Steps
----------

Now that Fast Channels is installed:

1. Read the :doc:`concepts` guide to understand consumers and channel layers
2. Follow the :doc:`tutorial/index` for a hands-on walkthrough
