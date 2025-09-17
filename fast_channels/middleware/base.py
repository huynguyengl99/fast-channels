"""Base middleware implementation for the fast-channels framework.

This module provides the abstract base class for implementing ASGI middleware
that can be used to wrap channel applications.
"""

from fast_channels.type_defs import (
    ASGIReceiveCallable,
    ASGISendCallable,
    ChannelApplication,
    ChannelScope,
)


class BaseMiddleware:
    """
    Base class for implementing ASGI middleware.

    Note that subclasses of this are not self-safe; don't store state on
    the instance, as it serves multiple application instances. Instead, use
    scope.
    """

    def __init__(self, inner: ChannelApplication):
        """
        Middleware constructor - just takes inner application.

        Args:
            inner: The inner ASGI application to wrap.
        """
        self.inner: ChannelApplication = inner

    async def __call__(
        self, scope: ChannelScope, receive: ASGIReceiveCallable, send: ASGISendCallable
    ) -> ChannelApplication:
        """
        ASGI application; can insert things into the scope and run asynchronous
        code.

        Args:
            scope: The ASGI scope dictionary.
            receive: ASGI receive callable.
            send: ASGI send callable.

        Returns:
            The result of calling the inner application.
        """
        # Copy scope to stop changes going upstream
        scope = dict(scope)
        # Run the inner application along with the scope
        return await self.inner(scope, receive, send)  # type: ignore
