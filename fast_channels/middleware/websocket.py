"""WebSocket-specific middleware for the fast-channels framework.

This module provides middleware for WebSocket connections, including
origin validation and connection denial capabilities.
"""

from collections.abc import Iterable
from typing import Any, TypeAlias, cast
from urllib.parse import ParseResult, urlparse

from fast_channels.consumer.websocket import AsyncWebsocketConsumer
from fast_channels.type_defs import (
    ASGIReceiveCallable,
    ASGISendCallable,
    ChannelApplication,
    ChannelScope,
)
from fast_channels.utils import is_same_domain

Origin: TypeAlias = str
"""Type alias for WebSocket origin strings."""

AllowedOrigins: TypeAlias = Iterable[Origin]
"""Type alias for collections of allowed origins."""


class OriginValidator:
    """
    Validates that the incoming connection has an Origin header that
    is in an allowed list.
    """

    def __init__(
        self, application: ChannelApplication, allowed_origins: AllowedOrigins
    ):
        self.application: ChannelApplication = application
        self.allowed_origins: AllowedOrigins = allowed_origins

    async def __call__(
        self, scope: ChannelScope, receive: ASGIReceiveCallable, send: ASGISendCallable
    ) -> Any:
        """Validate WebSocket origin and handle the connection.

        Args:
            scope: The ASGI scope for the WebSocket connection.
            receive: ASGI receive callable.
            send: ASGI send callable.

        Returns:
            Result from the application or WebSocket denier.

        Raises:
            ValueError: If used on a non-WebSocket connection.
        """
        # Make sure the scope is of type websocket
        if scope["type"] != "websocket":
            raise ValueError(
                "You cannot use OriginValidator on a non-WebSocket connection"
            )
        # Extract the Origin header
        parsed_origin = None
        for header_name, header_value in scope.get("headers", []):
            if header_name == b"origin":
                try:
                    # Set ResultParse
                    parsed_origin = cast(
                        ParseResult | None, urlparse(header_value.decode("latin1"))
                    )
                except UnicodeDecodeError:
                    pass
        # Check to see if the origin header is valid
        if self.valid_origin(parsed_origin):
            # Pass control to the application
            return await self.application(scope, receive, send)
        else:
            # Deny the connection
            denier = WebsocketDenier()
            return await denier(scope, receive, send)

    def valid_origin(self, parsed_origin: ParseResult | None) -> bool:
        """
        Checks parsed origin is None.

        Pass control to the validate_origin function.

        Returns ``True`` if validation function was successful, ``False`` otherwise.
        """
        # None is not allowed unless all hosts are allowed
        if parsed_origin is None and "*" not in self.allowed_origins:
            return False
        return self.validate_origin(parsed_origin)

    def validate_origin(self, parsed_origin: ParseResult | None) -> bool:
        """
        Validate the given origin for this site.

        Check than the origin looks valid and matches the origin pattern in
        specified list ``allowed_origins``. Any pattern begins with a scheme.
        After the scheme there must be a domain. Any domain beginning with a
        period corresponds to the domain and all its subdomains (for example,
        ``http://.example.com``). After the domain there must be a port,
        but it can be omitted. ``*`` matches anything and anything
        else must match exactly.

        Note. This function assumes that the given origin has a schema, domain
        and port, but port is optional.

        Returns ``True`` for a valid host, ``False`` otherwise.
        """
        return any(
            pattern == "*" or self.match_allowed_origin(parsed_origin, pattern)
            for pattern in self.allowed_origins
        )

    def match_allowed_origin(
        self, parsed_origin: ParseResult | None, pattern: str
    ) -> bool:
        """
        Returns ``True`` if the origin is either an exact match or a match
        to the wildcard pattern. Compares scheme, domain, port of origin and pattern.

        Any pattern can be begins with a scheme. After the scheme must be a domain,
        or just domain without scheme.
        Any domain beginning with a period corresponds to the domain and all
        its subdomains (for example, ``.example.com`` ``example.com``
        and any subdomain). Also with scheme (for example, ``http://.example.com``
        ``http://example.com``). After the domain there must be a port,
        but it can be omitted.

        Note. This function assumes that the given origin is either None, a
        schema-domain-port string, or just a domain string
        """
        if parsed_origin is None:
            return False

        # Get ResultParse object
        parsed_pattern = urlparse(pattern.lower())
        if parsed_origin.hostname is None:
            return False
        if not parsed_pattern.scheme:
            pattern_hostname = urlparse("//" + pattern).hostname or pattern
            return is_same_domain(parsed_origin.hostname, pattern_hostname)
        # Get origin.port or default ports for origin or None
        origin_port = self.get_origin_port(parsed_origin)
        # Get pattern.port or default ports for pattern or None
        pattern_port = self.get_origin_port(parsed_pattern)
        # Compares hostname, scheme, ports of pattern and origin
        if (
            parsed_pattern.scheme == parsed_origin.scheme
            and origin_port == pattern_port
            and is_same_domain(parsed_origin.hostname, parsed_pattern.hostname)  # type: ignore
        ):
            return True
        return False

    def get_origin_port(self, origin: ParseResult) -> int | None:
        """
        Returns the origin.port or port for this schema by default.
        Otherwise, it returns None.
        """
        if origin.port is not None:
            # Return origin.port
            return origin.port
        # if origin.port doesn`t exists
        if origin.scheme in {"http", "ws"}:
            # Default port return for http, ws
            return 80
        elif origin.scheme in {"https", "wss"}:
            # Default port return for https, wss
            return 443
        else:
            return None


class WebsocketDenier(AsyncWebsocketConsumer):
    """
    Simple application which denies all requests to it.
    """

    async def connect(self) -> None:
        """Handle connection by immediately denying it."""
        await self.close()
