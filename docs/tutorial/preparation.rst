Preparation
===========

*Setting Up Your Environment*

Before we start building our WebSocket application, let's set up the development environment with all the necessary
tools and dependencies.

Prerequisites
-------------

Make sure you have the following installed:

- **Python 3.11+** - Fast Channels requires Python 3.11 or higher
- **Docker** - For running Redis locally
- **uv** (recommended) or **pip** - For package management

Creating Your Project
---------------------

First, create a new directory for your tutorial project:

.. code-block:: bash

    mkdir tutorial-project
    cd tutorial-project

Now create the main project structure with a sandbox directory for your source code:

.. code-block:: bash

    mkdir sandbox

This structure matches the Fast Channels repository layout, where ``sandbox`` is the source directory at the same
level as ``pyproject.toml``.

Installing Dependencies
-----------------------

You'll need several packages for this tutorial. Choose your preferred package manager:

**Option 1: Using uv (Recommended)**

.. code-block:: bash

    # Create a virtual environment with seed packages
    uv venv --seed

    # Activate the virtual environment
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate

    # Add the required dependencies
    uv add fastapi "fast-channels[redis]" rq "uvicorn[standard]"

**Option 2: Using pip**

.. code-block:: bash

    # Create a virtual environment
    python -m venv .venv

    # Activate it
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate

    # Install dependencies
    pip install fastapi "fast-channels[redis]" rq "uvicorn[standard]"

**Required Dependencies Explained:**

- **fastapi** - Modern ASGI web framework for building APIs
- **fast-channels[redis]** - Fast Channels with Redis channel layer support
- **rq** - Redis Queue for background job processing
- **uvicorn[standard]** - ASGI server for running FastAPI applications

Setting Up Redis with Docker
----------------------------

Redis is required for channel layers in production. We'll use Docker Compose to run Redis locally.

Create a ``docker-compose.yml`` file in your project root directory (``tutorial-project/``):

.. code-block:: yaml

    services:
      redis:
        image: redis:7
        ports:
          - "6399:6379"
        networks:
          - fast-channels

    networks:
      fast-channels:
        driver: bridge

**Note:** We're using port 6399 instead of the default 6379 to avoid conflicts with any existing Redis installations.

Start Redis:

.. code-block:: bash

    docker compose up -d

You can verify Redis is running:

.. code-block:: bash

    docker compose ps

Project Structure
-----------------

Create the basic project structure:

.. code-block:: bash

    mkdir -p sandbox/static/css sandbox/static/js
    touch sandbox/__init__.py sandbox/main.py

Your project structure should look like this:

.. code-block:: text

    tutorial-project/
    ├── docker-compose.yml
    └── sandbox/
        ├── __init__.py
        ├── main.py
        └── static/
            ├── css/
            └── js/

Basic FastAPI Application
-------------------------

Create a basic FastAPI application in ``sandbox/main.py``:

.. literalinclude:: ../../sandbox/tutorial/main.py
   :language: python

This creates a basic FastAPI application with static file serving and a simple HTML page to get you started.

Adding JavaScript Functionality
-------------------------------

Create the JavaScript file at ``sandbox/static/js/main.js`` to handle WebSocket connections and user interactions:

.. raw:: html

   <details open>
   <summary><a>JavaScript content</a></summary>

.. literalinclude:: ../../sandbox/static/js/main.js
   :language: javascript

.. raw:: html

   </details>

This JavaScript file provides all the WebSocket connection handling, message sending, and UI interactions needed for the tutorial application.

Adding Basic Styles
-------------------

Create a basic CSS file at ``sandbox/static/css/style.css``:

.. raw:: html

   <details open>
   <summary><a>CSS content</a></summary>

.. literalinclude:: ../../sandbox/static/css/style.css
       :language: css

.. raw:: html

   </details>


This provides all the styles needed for the tutorial application including responsive layout, chat boxes, input forms,
and message styling.

Testing Your Setup
------------------

Let's test that everything is working:

1. **Start your FastAPI application:**

.. code-block:: bash

    uvicorn sandbox.main:app --reload --port 8080

2. **Visit your application:**

Open your browser and go to http://localhost:8080. You should see your basic FastAPI application.

.. image:: ../_static/tutorial_prepare.png
   :alt: Tutorial preparation setup result
   :align: center

Troubleshooting
---------------

**Common Issues:**

**Port Already in Use:**
   If port 8080 is busy, change the port in the uvicorn command: ``uvicorn sandbox.main:app --reload --port 8000``. You'll also need to update the WebSocket URLs in ``sandbox/static/js/main.js`` to match the new port (e.g., change ``ws://localhost:8080`` to ``ws://localhost:8000``)

**Redis Connection Issues:**
   Make sure Docker is running and the Redis container started successfully with ``docker compose ps``

**Import Errors:**
   Ensure you're in the correct directory and your virtual environment is activated

**Docker Permission Issues:**
   On Linux, you might need to run Docker commands with ``sudo`` or add your user to the docker group

Next Steps
----------

Great! You now have:

✅ A working FastAPI application

✅ Fast Channels installed with Redis support

✅ Redis running in Docker

✅ Basic project structure and styles

You're ready to start building WebSocket consumers! In the next section, we'll create our first WebSocket consumer
without channel layers to understand the basics.

Continue to :doc:`system-messages` to build your first WebSocket consumer.
