"""Custom exceptions for the fast-channels framework.

This module defines all custom exceptions used throughout the fast-channels
framework for error handling and flow control.
"""


class InvalidChannelLayerError(ValueError):
    """
    Raised when a channel layer is configured incorrectly.
    """

    pass


class AcceptConnection(Exception):
    """
    Raised during a websocket.connect (or other supported connection) handler
    to accept the connection.
    """

    pass


class DenyConnection(Exception):
    """
    Raised during a websocket.connect (or other supported connection) handler
    to deny the connection.
    """

    pass


class ChannelFull(Exception):
    """
    Raised when a channel cannot be sent to as it is over capacity.
    """

    pass


class MessageTooLarge(Exception):
    """
    Raised when a message cannot be sent as it's too big.
    """

    pass


class StopConsumer(Exception):
    """
    Raised when a consumer wants to stop and close down its application instance.
    """

    pass
