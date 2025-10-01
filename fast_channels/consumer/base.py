"""Base consumer implementations for the fast-channels framework.

This module provides the core consumer classes that handle ASGI applications
and provide the foundation for all channel-based message consumers.
"""

import functools
from typing import Any, cast

from fast_channels.exceptions import StopConsumer
from fast_channels.layers import BaseChannelLayer, get_channel_layer
from fast_channels.type_defs import (
    ASGIApplication,
    ASGIReceiveCallable,
    ASGISendCallable,
    ChannelMessage,
    ChannelScope,
)
from fast_channels.utils import await_many_dispatch


def get_handler_name(message: ChannelMessage) -> str:
    """
    Looks at a message, checks it has a sensible type, and returns the
    handler name for that type.

    Args:
        message: A channel message containing a 'type' field.

    Returns:
        The handler name for the message type with dots replaced by underscores.

    Raises:
        ValueError: If message has no 'type' attribute or type starts with underscore.
    """
    # Check message looks OK
    if "type" not in message:
        raise ValueError("Incoming message has no 'type' attribute")
    # Extract type and replace . with _
    handler_name = cast(str, message["type"].replace(".", "_"))
    if handler_name.startswith("_"):
        raise ValueError("Malformed type in message (leading underscore)")
    return handler_name


class AsyncConsumer:
    """
    Base consumer class. Implements the ASGI application spec, and adds on
    channel layer management and routing of events to named methods based
    on their type.
    """

    channel_layer_alias: str | None = None
    scope: ChannelScope
    channel_layer: BaseChannelLayer | None
    channel_name: str
    channel_receive: ASGIReceiveCallable
    base_send: ASGISendCallable

    async def __call__(
        self, scope: ChannelScope, receive: ASGIReceiveCallable, send: ASGISendCallable
    ) -> None:
        """
        Dispatches incoming messages to type-based handlers asynchronously.

        Args:
            scope: The ASGI scope for this consumer.
            receive: ASGI receive callable for receiving messages.
            send: ASGI send callable for sending messages.
        """
        self.scope = scope

        # Initialize channel layer
        self.channel_layer = (
            get_channel_layer(self.channel_layer_alias)
            if self.channel_layer_alias
            else None
        )
        if self.channel_layer is not None:
            self.channel_name = await self.channel_layer.new_channel()
            self.channel_receive = functools.partial(
                self.channel_layer.receive, self.channel_name
            )
        # Store send function
        self.base_send = send
        # Pass messages in from channel layer or client to dispatch method
        try:
            if self.channel_layer is not None:
                await await_many_dispatch(
                    [receive, self.channel_receive], self.dispatch
                )
            else:
                await await_many_dispatch([receive], self.dispatch)
        except StopConsumer:
            # Exit cleanly
            pass

    async def dispatch(self, message: ChannelMessage) -> None:
        """
        Works out what to do with a message.

        Args:
            message: The channel message to dispatch to appropriate handler.

        Raises:
            ValueError: If no handler exists for the message type.
        """
        handler = getattr(self, get_handler_name(message), None)
        if handler:
            await handler(message)
        else:
            raise ValueError("No handler for message type {}".format(message["type"]))

    async def send(self, message: ChannelMessage) -> None:
        """
        Overrideable/callable-by-subclasses send method.

        Args:
            message: The channel message to send.
        """
        await self.base_send(message)

    @classmethod
    def as_asgi(cls, **initkwargs: Any) -> Any:  # Compatible with all ASGI frameworks
        """
        Return an ASGI v3 single callable that instantiates a consumer instance
        per scope. Similar in purpose to Django's as_view().

        Args:
            **initkwargs: Keyword arguments used to instantiate the consumer instance.

        Returns:
            An ASGI application protocol wrapper that creates consumer instances.
        """

        class ASGIWrapper:
            """ASGI application wrapper for consumer classes."""

            def __init__(self, **initkwargs: Any):
                """Initialize the ASGI wrapper with consumer initialization arguments.

                Args:
                    **initkwargs: Keyword arguments for consumer initialization.
                """
                self.cls = cls
                self.initkwargs = initkwargs

            async def __call__(
                self,
                scope: ChannelScope,
                receive: ASGIReceiveCallable,
                send: ASGISendCallable,
            ) -> ASGIApplication | None:
                """Handle ASGI requests by instantiating and calling the consumer.

                Args:
                    scope: The ASGI scope for this request.
                    receive: ASGI receive callable for receiving messages.
                    send: ASGI send callable for sending messages.

                Returns:
                    None after handling the ASGI request.
                """
                instance = self.cls(**self.initkwargs)
                return await instance(scope, receive, send)  # type: ignore[func-returns-value]

        wrapper = ASGIWrapper()
        wrapper.consumer_class = cls  # type: ignore
        wrapper.consumer_initkwargs = initkwargs  # type: ignore

        # Take name and docstring from class
        functools.update_wrapper(wrapper, cls, updated=())
        return wrapper
