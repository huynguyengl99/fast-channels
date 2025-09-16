import asyncio
import random
import string
import time
from asyncio import Task
from copy import deepcopy
from typing import Any, TypeAlias

from fast_channels.exceptions import ChannelFull
from fast_channels.type_defs import ChannelCapacityDict, ChannelMessage

from .base import BaseChannelLayer

InMemoryQueueData: TypeAlias = tuple[float, ChannelMessage]
InMemoryGroups: TypeAlias = dict[str, dict[str, float]]


class InMemoryChannelLayer(BaseChannelLayer):
    """
    In-memory channel layer implementation compatible with Django Channels
    """

    def __init__(
        self,
        expiry: float = 60,
        group_expiry: float = 86400,
        capacity: int = 100,
        channel_capacity: ChannelCapacityDict | None = None,
    ):
        super().__init__(
            expiry=expiry,
            capacity=capacity,
            channel_capacity=channel_capacity,
        )
        self.channels: dict[str, asyncio.Queue[InMemoryQueueData]] = {}
        self.groups: InMemoryGroups = {}
        self.group_expiry: float = group_expiry

    # Channel layer API
    extensions = ["groups", "flush"]

    async def send(self, channel: str, message: ChannelMessage) -> None:
        """
        Send a message onto a (general or specific) channel.
        """
        # Typecheck
        assert isinstance(message, dict), "message is not a dict"
        self.require_valid_channel_name(channel)
        # If it's a process-local channel, strip off local part and stick full
        # name in message
        assert "__asgi_channel__" not in message

        queue = self.channels.setdefault(
            channel, asyncio.Queue(maxsize=self.get_capacity(channel))
        )
        # Add message
        try:
            queue.put_nowait((time.time() + self.expiry, deepcopy(message)))
        except asyncio.QueueFull:
            raise ChannelFull(channel) from None

    async def receive(self, channel: str) -> ChannelMessage:
        """
        Receive the first message that arrives on the channel.
        If more than one coroutine waits on the same channel, a random one
        of the waiting coroutines will get the result.
        """
        self.require_valid_channel_name(channel)
        self._clean_expired()

        queue = self.channels.setdefault(
            channel,
            asyncio.Queue[InMemoryQueueData](maxsize=self.get_capacity(channel)),
        )

        # Do a plain direct receive
        try:
            _, message = await queue.get()
        finally:
            if queue.empty():
                self.channels.pop(channel, None)

        return message

    async def new_channel(self, prefix: str = "specific.") -> str:
        """
        Returns a new channel name that can be used by something in our
        process as a specific channel.
        """
        return "{}.inmemory!{}".format(
            prefix,
            "".join(random.choice(string.ascii_letters) for _ in range(12)),
        )

    # Expire cleanup
    def _clean_expired(self) -> None:
        """
        Goes through all messages and groups and removes those that are expired.
        Any channel with an expired message is removed from all groups.
        """
        # Channel cleanup
        for channel, queue in list(self.channels.items()):
            # See if it's expired
            while not queue.empty() and queue._queue[0][0] < time.time():  # type: ignore[attr-defined]
                queue.get_nowait()
                # Any removal prompts group discard
                self._remove_from_groups(channel)
                # Is the channel now empty and needs deleting?
                if queue.empty():
                    self.channels.pop(channel, None)

        # Group Expiration
        timeout = int(time.time()) - self.group_expiry
        for channels in self.groups.values():
            for name, timestamp in list(channels.items()):
                # If join time is older than group_expiry
                # end the group membership
                if timestamp and timestamp < timeout:
                    # Delete from group
                    channels.pop(name, None)

    # Flush extension
    async def flush(self) -> None:
        self.channels = {}
        self.groups = {}

    async def close(self) -> None:
        # Nothing to go
        pass

    def _remove_from_groups(self, channel: str) -> None:
        """
        Removes a channel from all groups. Used when a message on it expires.
        """
        for channels in self.groups.values():
            channels.pop(channel, None)

    # Groups extension
    async def group_add(self, group: str, channel: str) -> None:
        """
        Adds the channel name to a group.
        """
        # Check the inputs
        self.require_valid_group_name(group)
        self.require_valid_channel_name(channel)
        # Add to group dict
        self.groups.setdefault(group, {})
        self.groups[group][channel] = time.time()

    async def group_discard(self, group: str, channel: str) -> None:
        # Both should be text and valid
        self.require_valid_channel_name(channel)
        self.require_valid_group_name(group)
        # Remove from group set
        group_channels = self.groups.get(group, None)
        if group_channels:
            # remove channel if in group
            group_channels.pop(channel, None)
            # is group now empty? If yes remove it
            if not group_channels:
                self.groups.pop(group, None)

    async def group_send(self, group: str, message: ChannelMessage) -> None:
        # Check types
        assert isinstance(message, dict), "Message is not a dict"
        self.require_valid_group_name(group)
        # Run clean
        self._clean_expired()

        # Send to each channel
        ops: list[Task[Any]] = []
        if group in self.groups:
            for channel in self.groups[group].keys():
                ops.append(asyncio.create_task(self.send(channel, message)))
        for send_result in asyncio.as_completed(ops):
            try:
                await send_result
            except ChannelFull:
                pass
