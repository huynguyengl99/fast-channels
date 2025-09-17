"""Base channel layer implementation.

This module provides the abstract base class for all channel layer implementations
in the fast-channels framework, defining the standard interface and common utilities.
"""

import fnmatch
import re

from fast_channels.type_defs import (
    ChannelCapacityDict,
    ChannelMessage,
    CompiledChannelCapacities,
)


class BaseChannelLayer:
    """
    Base channel layer class that others can inherit from, with useful
    common functionality.
    """

    MAX_NAME_LENGTH: int = 100
    expiry: float
    capacity: int
    channel_capacity: CompiledChannelCapacities

    def __init__(
        self,
        expiry: float = 60,
        capacity: int = 100,
        channel_capacity: ChannelCapacityDict | None = None,
    ):
        """Initialize the base channel layer.

        Args:
            expiry: Message expiry time in seconds (default: 60).
            capacity: Default channel capacity (default: 100).
            channel_capacity: Dict mapping channel patterns to specific capacities.
        """
        self.expiry = expiry
        self.capacity = capacity
        self.channel_capacity = self.compile_capacities(channel_capacity or {})

    def compile_capacities(
        self, channel_capacity: ChannelCapacityDict
    ) -> CompiledChannelCapacities:
        """
        Takes an input channel_capacity dict and returns the compiled list
        of regexes that get_capacity will look for as self.channel_capacity

        Args:
            channel_capacity: Dictionary mapping channel patterns to capacities.

        Returns:
            List of compiled regex patterns with their associated capacities.
        """
        result: CompiledChannelCapacities = []
        for pattern, value in channel_capacity.items():
            # If they passed in a precompiled regex, leave it, else interpret
            # it as a glob.
            if isinstance(pattern, re.Pattern):
                # It's already compiled, use it directly
                result.append((pattern, value))
            else:
                # It's a string, compile it as a glob pattern
                compiled_pattern = re.compile(fnmatch.translate(pattern))
                result.append((compiled_pattern, value))
        return result

    def get_capacity(self, channel: str) -> int:
        """
        Gets the correct capacity for the given channel; either the default,
        or a matching result from channel_capacity. Returns the first matching
        result; if you want to control the order of matches, use an ordered dict
        as input.

        Args:
            channel: The channel name to get capacity for.

        Returns:
            The capacity for the given channel.
        """
        for pattern, capacity in self.channel_capacity:
            if pattern.match(channel):
                return capacity
        return self.capacity

    def match_type_and_length(self, name: str | object) -> bool:
        """Check if a name is a valid string with acceptable length.

        Args:
            name: The name to validate.

        Returns:
            True if name is a string shorter than MAX_NAME_LENGTH.
        """
        if isinstance(name, str) and (len(name) < self.MAX_NAME_LENGTH):
            return True
        return False

    # Name validation functions
    channel_name_regex = re.compile(r"^[a-zA-Z\d\-_.]+(\![\d\w\-_.]*)?$")
    group_name_regex = re.compile(r"^[a-zA-Z\d\-_.]+$")
    invalid_name_error = (
        "{} name must be a valid unicode string "
        + f"with length < {MAX_NAME_LENGTH} "
        + "containing only ASCII alphanumerics, hyphens, underscores, or periods."
    )

    def require_valid_channel_name(self, name: str, receive: bool = False) -> bool:
        """Validate a channel name according to the naming rules.

        Args:
            name: The channel name to validate.
            receive: Whether this name will be used for receiving messages.

        Returns:
            True if the name is valid.

        Raises:
            TypeError: If the channel name is invalid.
        """
        if not self.match_type_and_length(name):
            raise TypeError(self.invalid_name_error.format("Channel"))
        if not bool(self.channel_name_regex.match(name)):
            raise TypeError(self.invalid_name_error.format("Channel"))
        if "!" in name and not name.endswith("!") and receive:
            raise TypeError("Specific channel names in receive() must end at the !")
        return True

    def require_valid_group_name(self, name: str) -> bool:
        """Validate a group name according to the naming rules.

        Args:
            name: The group name to validate.

        Returns:
            True if the name is valid.

        Raises:
            TypeError: If the group name is invalid.
        """
        if not self.match_type_and_length(name):
            raise TypeError(self.invalid_name_error.format("Group"))
        if not bool(self.group_name_regex.match(name)):
            raise TypeError(self.invalid_name_error.format("Group"))
        return True

    def non_local_name(self, name: str) -> str:
        """
        Given a channel name, returns the "non-local" part. If the channel name
        is a process-specific channel (contains !) this means the part up to
        and including the !; if it is anything else, this means the full name.

        Args:
            name: The channel name to process.

        Returns:
            The non-local part of the channel name.
        """
        if "!" in name:
            return name[: name.find("!") + 1]
        else:
            return name

    async def send(self, channel: str, message: ChannelMessage) -> None:
        """Send a message to a channel.

        Args:
            channel: The channel name to send to.
            message: The message to send.

        Raises:
            NotImplementedError: Must be implemented by subclasses.
        """
        raise NotImplementedError("send() should be implemented in a channel layer")

    async def receive(self, channel: str) -> ChannelMessage:
        """Receive a message from a channel.

        Args:
            channel: The channel name to receive from.

        Returns:
            The received message.

        Raises:
            NotImplementedError: Must be implemented by subclasses.
        """
        raise NotImplementedError("receive() should be implemented in a channel layer")

    async def new_channel(self, prefix: str = "specific.") -> str:
        """Generate a new unique channel name.

        Args:
            prefix: Prefix for the new channel name.

        Returns:
            A unique channel name.

        Raises:
            NotImplementedError: Must be implemented by subclasses.
        """
        raise NotImplementedError(
            "new_channel() should be implemented in a channel layer"
        )

    async def flush(self) -> None:
        """Flush all messages from all channels.

        Raises:
            NotImplementedError: Must be implemented by subclasses that support flushing.
        """
        raise NotImplementedError("flush() not implemented (flush extension)")

    async def group_add(self, group: str, channel: str) -> None:
        """Add a channel to a group.

        Args:
            group: The group name.
            channel: The channel name to add to the group.

        Raises:
            NotImplementedError: Must be implemented by subclasses that support groups.
        """
        raise NotImplementedError("group_add() not implemented (groups extension)")

    async def group_discard(self, group: str, channel: str) -> None:
        """Remove a channel from a group.

        Args:
            group: The group name.
            channel: The channel name to remove from the group.

        Raises:
            NotImplementedError: Must be implemented by subclasses that support groups.
        """
        raise NotImplementedError("group_discard() not implemented (groups extension)")

    async def group_send(self, group: str, message: ChannelMessage) -> None:
        """Send a message to all channels in a group.

        Args:
            group: The group name to send to.
            message: The message to send.

        Raises:
            NotImplementedError: Must be implemented by subclasses that support groups.
        """
        raise NotImplementedError("group_send() not implemented (groups extension)")
