Introduction
============

Welcome to Fast Channels!

Fast Channels brings the proven patterns of Django Channels to the entire ASGI ecosystem, enabling real-time WebSocket applications for FastAPI, Starlette, and any ASGI-compatible framework.

Why Fast Channels?
~~~~~~~~~~~~~~~~~~

After years of working with Django Channels in production environments, we fell in love with its powerful approach to real-time communication:

- **Group Messaging**: The ability to send messages to multiple WebSocket connections simultaneously
- **Cross-Process Communication**: Send messages from background workers, HTTP endpoints, or other processes to WebSocket clients
- **Real-time Notifications**: Perfect for live updates, chat systems, and streaming applications

However, when working with FastAPI and Starlette projects, we couldn't find a comparable solution that provided the same level of functionality and developer experience. Existing alternatives were either too simple (basic pub/sub) or required heavy architectural changes.

That's why we created Fast Channels - to bring Django's battle-tested WebSocket patterns to the modern ASGI ecosystem.

The Django Channels Inspiration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Django Channels revolutionized real-time web development by introducing the concept of **consumers** - long-running application instances that handle WebSocket connections and other persistent protocols. This approach provides several key advantages:

**Event-Driven Architecture**
   Instead of handling just HTTP request/response cycles, consumers can process a continuous stream of events throughout a connection's lifetime.

**Familiar Programming Model**
   Write WebSocket handlers that feel similar to Django views, with clear methods for ``connect``, ``receive``, and ``disconnect`` events.

**Channel Layers for Scale**
   Enable communication between different processes and application instances, essential for building distributed real-time applications.

What Fast Channels Brings to ASGI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Fast Channels ports these proven concepts to work with any ASGI framework:

**Universal Compatibility**
   Works with FastAPI, Starlette, Quart, and any other ASGI-compatible framework without requiring Django.

**Production-Ready Patterns**
   Leverages Redis for reliable, high-performance message delivery - the same backend trusted by Django Channels in production.

**Developer Experience**
   Maintains the familiar consumer pattern while adding full type safety and modern Python async/await support.

**Flexible Architecture**
   Choose between different channel layer backends based on your needs - from simple in-memory layers for testing to Redis-backed solutions for production.

Getting Started
~~~~~~~~~~~~~~~

Fast Channels follows the same core concepts as Django Channels but adapted for the ASGI ecosystem:

1. **Consumers** handle WebSocket connections and define how your application responds to events
2. **Channel Layers** enable communication between different parts of your application

The key difference is that instead of Django's configuration-based approach, Fast Channels uses a **registry pattern** where you explicitly register channel layers and reference them in your consumers. For routing, you use your ASGI framework's native routing system (FastAPI's routing, Starlette's routing, etc.).

This approach provides better control and type safety while maintaining the proven architecture that has powered countless real-time Django applications.

Ready to dive in? Check out our :doc:`installation` guide to get started, or jump straight to the :doc:`tutorial/index` for a hands-on introduction.
