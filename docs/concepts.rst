Core Concepts
=============

Before diving into Fast Channels, it's important to understand the two fundamental building blocks:
**Consumers** and **Channel Layers**. These concepts form the foundation of real-time communication in Fast Channels.

Consumers
---------

A consumer is the heart of your WebSocket application - it's where you define how your application responds to
WebSocket events like connections, messages, and disconnections.

Consumer Types
~~~~~~~~~~~~~~

Fast Channels provides three main consumer classes to choose from:

**AsyncConsumer**
   The base consumer class that handles any ASGI protocol. Use this for custom protocols or when you need
   low-level control over message handling.

**AsyncWebsocketConsumer**
   The most commonly used consumer for WebSocket connections. Provides convenient methods for handling WebSocket
   events and automatic group management.

**AsyncJsonWebsocketConsumer**
   Extends AsyncWebsocketConsumer with automatic JSON encoding/decoding. Perfect for applications that primarily
   exchange JSON data.

Basic WebSocket Consumer Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Most applications will use ``AsyncWebsocketConsumer`` which implements three main methods:

.. code-block:: python

    from fast_channels.consumer.websocket import AsyncWebsocketConsumer

    class ChatConsumer(AsyncWebsocketConsumer):

        async def connect(self):
            # Called when a WebSocket connection is opened
            await self.accept()  # Accept the connection

        async def receive(self, text_data=None, bytes_data=None, **kwargs):
            # Called when a message is received from the client
            await self.send(text_data="Echo: " + text_data)

        async def disconnect(self, close_code):
            # Called when the WebSocket connection is closed
            pass

Key Consumer Methods
~~~~~~~~~~~~~~~~~~~~

**Connection Management:**

- ``accept()`` - Accept an incoming WebSocket connection

- ``close()`` - Close the WebSocket connection

- ``send(text_data, bytes_data)`` - Send text or binary data to the client

**JSON Consumer Methods (AsyncJsonWebsocketConsumer):**

- ``send_json(content)`` - Automatically encode and send JSON data

- ``receive_json(content)`` - Override this to handle incoming JSON messages

- ``encode_json(content)`` / ``decode_json(text_data)`` - Customize JSON serialization

**Groups:**
Define a ``groups`` list to automatically join/leave groups on connect/disconnect:

.. code-block:: python

    class ChatConsumer(AsyncWebsocketConsumer):
        groups = ["chat_room", "notifications"]  # Auto-join these groups

**Dynamic Group Management:**
For more flexibility, manually manage groups based on URL parameters or user data:

.. code-block:: python

    class RoomChatConsumer(AsyncWebsocketConsumer):
        channel_layer_alias = "chat"

        async def connect(self):
            # Extract room name from path parameters: /ws/room/{room_name}/
            self.room_name = self.scope['path_params']['room_name']
            self.room_group = f'room_{self.room_name}'

            # Extract user ID from query params: /ws/room/123/?user_id=456
            query_string = self.scope['query_string'].decode()
            # Parse query_string manually or use urllib.parse.parse_qs

            await self.accept()

            # Join room-specific group
            await self.channel_layer.group_add(self.room_group, self.channel_name)

        async def disconnect(self, close_code):
            # Leave the group
            await self.channel_layer.group_discard(self.room_group, self.channel_name)

The Scope - Your Request Context
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Every consumer has access to ``self.scope``, which contains connection information similar to a Django request object:

- ``scope["path"]`` - The WebSocket URL path
- ``scope["query_string"]`` - URL query parameters as bytes
- ``scope["headers"]`` - HTTP headers from the connection
- ``scope["cookies"]`` - Cookies sent by the client
- ``scope["user"]`` - User object (if authentication middleware is used)

This information is useful for authentication, routing users to specific groups, or customizing behavior based on
the connection:

.. code-block:: python

    async def connect(self):
        # Get user from scope
        user = self.scope.get("user")
        if user and user.is_authenticated:
            # Join user-specific group
            room_id = self.scope["path"].split("/")[-1]
            await self.accept()
        else:
            await self.close()

Why Async Only?
~~~~~~~~~~~~~~~

Unlike Django Channels, Fast Channels focuses exclusively on async consumers. This decision reflects the async-native
nature of modern ASGI frameworks like FastAPI and Starlette. Since these frameworks are built around async/await
patterns, using async consumers provides:

- Better performance and resource utilization
- Seamless integration with existing async codebases
- Elimination of complex sync-to-async conversions

Channel Layers
--------------

Without channel layers, your WebSocket consumer can only communicate directly with its connected client - like a
simple client-server connection. Channel layers unlock the real power of real-time applications by enabling
**cross-process communication**.

Setting Up Channel Layers
~~~~~~~~~~~~~~~~~~~~~~~~~

Before using channel layers, you need to **register them first** and then reference them in your consumers:

.. code-block:: python

    # Register a channel layer
    from fast_channels.layers import register_channel_layer, RedisChannelLayer

    register_channel_layer("chat", RedisChannelLayer(hosts=["redis://localhost:6379"]))

    # Use it in your consumer
    class ChatConsumer(AsyncWebsocketConsumer):
        channel_layer_alias = "chat"  # Reference the registered layer
        groups = ["chat_room"]

What Channel Layers Enable
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Group Messaging:**
Send messages to multiple WebSocket connections simultaneously. Perfect for chat rooms, live updates, or broadcasting
notifications.

**Background Worker Integration:**
Send messages from HTTP endpoints, background tasks, or separate processes to WebSocket clients. This enables patterns
like:

- HTTP API triggering real-time notifications
- Background jobs sending progress updates
- System events broadcasting to connected users

**Multi-Instance Applications:**
Scale your application across multiple processes or servers while maintaining real-time communication between all parts.

Core Channel Layer Operations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Send to Specific Connection:**

.. code-block:: python

    # Send a message to a specific channel (connection)
    await channel_layer.send(channel_name, {
        "type": "notification.message",
        "content": "Your order is ready!"
    })

**Send to Groups:**

.. code-block:: python

    # Broadcast to all connections in a group
    await channel_layer.group_send("chat_room_1", {
        "type": "chat.message",
        "username": "Alice",
        "message": "Hello everyone!"
    })

**Group Management:**

.. code-block:: python

    # Add a connection to a group
    await channel_layer.group_add("notifications", self.channel_name)

    # Remove a connection from a group
    await channel_layer.group_discard("notifications", self.channel_name)

How Messages Flow
~~~~~~~~~~~~~~~~~

When you send a message through the channel layer, it gets routed to the appropriate consumer method based on the
message ``type``. The type uses dot notation, which gets converted to method names:

- ``"chat.message"`` → calls ``chat_message()`` method
- ``"user.notification"`` → calls ``user_notification()`` method
- ``"system.alert"`` → calls ``system_alert()`` method

.. code-block:: python

    class ChatConsumer(AsyncWebsocketConsumer):

        async def receive(self, text_data=None, **kwargs):
            # User sends a message, broadcast it to the group
            await self.channel_layer.group_send("chat_room", {
                "type": "chat.message",
                "message": text_data,
                "username": "user123"
            })

        async def chat_message(self, event):
            # Handle the broadcast message and send to WebSocket
            await self.send_json({
                "message": event["message"],
                "username": event["username"]
            })

Channel Layer Backends
~~~~~~~~~~~~~~~~~~~~~~

Fast Channels supports multiple channel layer backends:

**In-Memory (Testing Only):**
- Single process only
- Perfect for unit tests and development
- Cannot communicate across processes

**Redis Queue Layer (Production):**
- Reliable message delivery with persistence
- Supports multiple processes and servers
- Best for critical messaging where delivery matters

**Redis Pub/Sub Layer (Real-time):**
- Ultra-low latency for live communication
- No message persistence
- Perfect for chat and live updates

The choice of backend depends on your specific needs - use in-memory for testing, Redis Queue for reliability, or
Redis Pub/Sub for speed.

Putting It Together
-------------------

Consumers and channel layers work together to create powerful real-time applications:

1. **Consumers** handle WebSocket connections and define your application logic
2. **Channel layers** enable communication between different parts of your system
3. **Groups** allow you to organize and broadcast to multiple connections
4. **Message routing** automatically dispatches channel layer messages to the right consumer methods

This architecture enables you to build anything from simple chat applications to complex distributed systems with
real-time updates, all while maintaining clean, readable code that leverages the proven patterns from Django Channels.

Ready to see this in action? Check out our :doc:`tutorial/index` for a hands-on walkthrough of building a real-time
application with Fast Channels.
