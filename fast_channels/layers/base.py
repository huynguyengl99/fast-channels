import fnmatch
import re

from fast_channels.types import (
    ChannelCapacityDict,
    ChannelMessage,
    CompiledChannelCapacity,
)


class BaseChannelLayer:
    """
    Base channel layer class that others can inherit from, with useful
    common functionality. Compatible with Django Channels API.
    """

    MAX_NAME_LENGTH: int = 100
    expiry: int
    capacity: int
    channel_capacity: ChannelCapacityDict | CompiledChannelCapacity

    def __init__(
        self,
        expiry: int = 60,
        capacity: int = 100,
        channel_capacity: ChannelCapacityDict | None = None,
    ):
        self.expiry = expiry
        self.capacity = capacity
        self.channel_capacity = self.compile_capacities(channel_capacity or {})

    def compile_capacities(
        self, channel_capacity: ChannelCapacityDict
    ) -> CompiledChannelCapacity:
        """
        Takes an input channel_capacity dict and returns the compiled list
        of regexes that get_capacity will look for as self.channel_capacity
        """
        result = []
        for pattern, value in channel_capacity.items():
            # If they passed in a precompiled regex, leave it, else interpret
            # it as a glob.
            if hasattr(pattern, "match"):
                result.append((pattern, value))
            else:
                result.append((re.compile(fnmatch.translate(pattern)), value))
        return result

    def get_capacity(self, channel: str) -> int:
        """
        Gets the correct capacity for the given channel; either the default,
        or a matching result from channel_capacity. Returns the first matching
        result; if you want to control the order of matches, use an ordered dict
        as input.
        """
        for pattern, capacity in self.channel_capacity:
            if pattern.match(channel):
                return capacity
        return self.capacity

    def match_type_and_length(self, name: str | object) -> bool:
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

    def require_valid_channel_name(
        self, name: str | object, receive: bool = False
    ) -> bool:
        if not self.match_type_and_length(name):
            raise TypeError(self.invalid_name_error.format("Channel"))
        if not bool(self.channel_name_regex.match(name)):
            raise TypeError(self.invalid_name_error.format("Channel"))
        if "!" in name and not name.endswith("!") and receive:
            raise TypeError("Specific channel names in receive() must end at the !")
        return True

    def require_valid_group_name(self, name: str | object) -> bool:
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
        """
        if "!" in name:
            return name[: name.find("!") + 1]
        else:
            return name

    async def send(self, channel: str, message: ChannelMessage) -> None:
        raise NotImplementedError("send() should be implemented in a channel layer")

    async def receive(self, channel: str) -> ChannelMessage:
        raise NotImplementedError("receive() should be implemented in a channel layer")

    async def new_channel(self, prefix: str = "specific.") -> str:
        raise NotImplementedError(
            "new_channel() should be implemented in a channel layer"
        )

    async def flush(self) -> None:
        raise NotImplementedError("flush() not implemented (flush extension)")

    async def group_add(self, group: str, channel: str) -> None:
        raise NotImplementedError("group_add() not implemented (groups extension)")

    async def group_discard(self, group: str, channel: str) -> None:
        raise NotImplementedError("group_discard() not implemented (groups extension)")

    async def group_send(self, group: str, message: str) -> None:
        raise NotImplementedError("group_send() not implemented (groups extension)")
