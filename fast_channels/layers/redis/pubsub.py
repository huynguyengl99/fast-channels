# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false

"""Redis Pub/Sub channel layer implementation.

This module provides a Redis-based channel layer implementation using Redis Pub/Sub
for message delivery with support for sharding across multiple Redis instances.
"""

import asyncio
import functools
import logging
import uuid
from asyncio import AbstractEventLoop, Future
from typing import Any, Literal, TypeAlias, cast

from redis import asyncio as aioredis
from redis.asyncio.client import PubSub

from fast_channels.layers import BaseChannelLayer
from fast_channels.type_defs import ChannelMessage

from .serializers import registry
from .type_defs import (
    ChannelDecodedRedisHost,
    ChannelRawRedisHost,
    SymmetricEncryptionKeys,
)
from .utils import (
    close_redis,
    consistent_hash,
    create_pool,
    decode_hosts,
    wrap_close,
)

logger = logging.getLogger(__name__)


async def _async_proxy(
    obj: "RedisPubSubChannelLayer", name: str, *args: Any, **kwargs: Any
) -> Any:
    """Async proxy function for delegating calls to loop-specific layer instances.

    Must be defined as a function and not a method due to
    https://bugs.python.org/issue38364

    Args:
        obj: The RedisPubSubChannelLayer instance.
        name: The method name to call on the loop layer.
        *args: Positional arguments to pass to the method.
        **kwargs: Keyword arguments to pass to the method.

    Returns:
        The result of the method call.
    """
    layer = obj._get_layer()  # pyright: ignore[reportPrivateUsage]
    return await getattr(layer, name)(*args, **kwargs)


CachedRedisPubSubLayers: TypeAlias = dict[AbstractEventLoop, "RedisPubSubLoopLayer"]
"""Type alias for cache mapping event loops to their Redis Pub/Sub layer instances."""


class RedisPubSubChannelLayer(BaseChannelLayer):
    """Redis Pub/Sub channel layer with event loop isolation.

    This class acts as a proxy that delegates operations to loop-specific
    RedisPubSubLoopLayer instances to ensure proper async context isolation.
    """

    def __init__(
        self,
        *args: Any,
        symmetric_encryption_keys: SymmetricEncryptionKeys | None = None,
        serializer_format: Literal["msgpack", "json"] | str = "msgpack",
        **kwargs: Any,
    ) -> None:
        """Initialize the Redis Pub/Sub channel layer.

        Args:
            *args: Arguments to pass to the loop layer constructor.
            symmetric_encryption_keys: Keys for message encryption.
            serializer_format: Message serialization format ("msgpack" or "json").
            **kwargs: Additional keyword arguments for the loop layer.
        """
        self._args = args
        self._kwargs = kwargs
        self._layers: CachedRedisPubSubLayers = {}
        # serialization
        self._serializer = registry.get_serializer(
            serializer_format,
            symmetric_encryption_keys=symmetric_encryption_keys,
        )

    def __getattribute__(self, name: str) -> Any:
        """Proxy method calls to the appropriate loop-specific layer instance.

        Args:
            name: The attribute/method name being accessed.

        Returns:
            The attribute value or a partial function for async methods.
        """
        # Check if this is one of the methods we want to proxy to the loop layer
        if name in (
            "new_channel",
            "send",
            "receive",
            "group_add",
            "group_discard",
            "group_send",
            "flush",
        ):
            return functools.partial(_async_proxy, self, name)

        # For all other attributes, use normal attribute lookup
        try:
            return super().__getattribute__(name)
        except AttributeError:
            # If attribute not found, try to get it from the loop layer
            return getattr(self._get_layer(), name)

    def serialize(self, message: ChannelMessage) -> bytes:
        """
        Serializes message to a byte string.
        """
        return self._serializer.serialize(message)

    def deserialize(self, message: bytes) -> ChannelMessage:
        """
        Deserializes from a byte string.
        """
        return cast(ChannelMessage, self._serializer.deserialize(message))

    def _get_layer(self) -> "RedisPubSubLoopLayer":
        """Get or create a loop-specific Redis Pub/Sub layer instance.

        Returns:
            The RedisPubSubLoopLayer instance for the current event loop.
        """
        loop = asyncio.get_running_loop()

        try:
            layer = self._layers[loop]
        except KeyError:
            layer = RedisPubSubLoopLayer(
                *self._args,
                **self._kwargs,
                channel_layer=self,  # type: ignore[misc]
            )
            self._layers[loop] = layer
            wrap_close(self, loop)

        return layer


class RedisPubSubLoopLayer:
    """Event loop-specific Redis Pub/Sub channel layer implementation.

    This class provides the actual Redis Pub/Sub functionality for a specific
    event loop, handling message routing and Redis connection management.
    """

    def __init__(
        self,
        hosts: list[ChannelRawRedisHost] | None = None,
        prefix: str = "asgi",
        on_disconnect: Any = None,
        on_reconnect: Any = None,
        channel_layer: RedisPubSubChannelLayer | None = None,
        **kwargs: Any,
    ):
        """Initialize the Redis Pub/Sub loop layer.

        Args:
            hosts: List of Redis host configurations.
            prefix: Prefix for Redis keys.
            on_disconnect: Callback for disconnect events.
            on_reconnect: Callback for reconnect events.
            channel_layer: Parent channel layer instance.
            **kwargs: Additional keyword arguments.
        """
        self.prefix = prefix

        self.on_disconnect = on_disconnect
        self.on_reconnect = on_reconnect
        assert channel_layer is not None
        self.channel_layer: RedisPubSubChannelLayer = channel_layer

        # Each consumer gets its own *specific* channel, created with the `new_channel()` method.
        # This dict maps `channel_name` to a queue of messages for that channel.
        self.channels: dict[str, asyncio.Queue[Any]] = {}

        # A channel can subscribe to zero or more groups.
        # This dict maps `group_name` to set of channel names who are subscribed to that group.
        self.groups: dict[str, set[str]] = {}

        # For each host, we create a `RedisSingleShardConnection` to manage the connection to that host.
        self._shards = [
            RedisSingleShardConnection(host, self) for host in decode_hosts(hosts)
        ]

    def _get_shard(self, channel_or_group_name: str) -> "RedisSingleShardConnection":
        """
        Return the shard that is used exclusively for this channel or group.
        """
        return self._shards[consistent_hash(channel_or_group_name, len(self._shards))]

    def _get_group_channel_name(self, group: str) -> str:
        """
        Return the channel name used by a group.
        Includes '__group__' in the returned
        string so that these names are distinguished
        from those returned by `new_channel()`.
        Technically collisions are possible, but it
        takes what I believe is intentional abuse in
        order to have colliding names.
        """
        return f"{self.prefix}__group__{group}"

    async def _subscribe_to_channel(self, channel: str) -> None:
        """Subscribe to a Redis channel and create a local message queue.

        Args:
            channel: The channel name to subscribe to.
        """
        self.channels[channel] = asyncio.Queue()
        shard = self._get_shard(channel)
        await shard.subscribe(channel)

    extensions = ["groups", "flush"]

    ################################################################################
    # Channel layer API
    ################################################################################

    async def send(self, channel: str, message: ChannelMessage) -> None:
        """
        Send a message onto a (general or specific) channel.
        """
        shard = self._get_shard(channel)
        await shard.publish(channel, self.channel_layer.serialize(message))

    async def new_channel(self, prefix: str = "specific.") -> str:
        """
        Returns a new channel name that can be used by a consumer in our
        process as a specific channel.
        """
        channel = f"{self.prefix}{prefix}{uuid.uuid4().hex}"
        await self._subscribe_to_channel(channel)
        return channel

    async def receive(self, channel: str) -> ChannelMessage:
        """
        Receive the first message that arrives on the channel.
        If more than one coroutine waits on the same channel, a random one
        of the waiting coroutines will get the result.
        """
        if channel not in self.channels:
            await self._subscribe_to_channel(channel)

        q = self.channels[channel]
        try:
            message = await q.get()
        except (TimeoutError, asyncio.CancelledError, GeneratorExit):
            # We assume here that the reason we are cancelled is because the consumer
            # is exiting, therefore we need to cleanup by unsubscribe below. Indeed,
            # currently the way that Django Channels works, this is a safe assumption.
            # In the future, Django Channels could change to call a *new* method that
            # would serve as the antithesis of `new_channel()`; this new method might
            # be named `delete_channel()`. If that were the case, we would do the
            # following cleanup from that new `delete_channel()` method, but, since
            # that's not how Django Channels works (yet), we do the cleanup below:
            if channel in self.channels:
                del self.channels[channel]
                try:
                    shard = self._get_shard(channel)
                    await shard.unsubscribe(channel)
                except BaseException:
                    logger.exception("Unexpected exception while cleaning-up channel:")
                    # We don't re-raise here because we want the CancelledError to be the one re-raised.
            raise

        return self.channel_layer.deserialize(message)

    ################################################################################
    # Groups extension
    ################################################################################

    async def group_add(self, group: str, channel: str) -> None:
        """
        Adds the channel name to a group.
        """
        if channel not in self.channels:
            raise RuntimeError(
                "You can only call group_add() on channels that exist in-process.\n"
                "Consumers are encouraged to use the common pattern:\n"
                f"   self.channel_layer.group_add({repr(group)}, self.channel_name)"
            )
        group_channel = self._get_group_channel_name(group)
        if group_channel not in self.groups:
            self.groups[group_channel] = set()
        group_channels = self.groups[group_channel]
        if channel not in group_channels:
            group_channels.add(channel)
        shard = self._get_shard(group_channel)
        await shard.subscribe(group_channel)

    async def group_discard(self, group: str, channel: str) -> None:
        """
        Removes the channel from a group if it is in the group;
        does nothing otherwise (does not error)
        """
        group_channel = self._get_group_channel_name(group)
        group_channels = self.groups.get(group_channel, set())
        if channel not in group_channels:
            return

        group_channels.remove(channel)
        if len(group_channels) == 0:
            del self.groups[group_channel]
            shard = self._get_shard(group_channel)
            await shard.unsubscribe(group_channel)

    async def group_send(self, group: str, message: ChannelMessage) -> None:
        """
        Send the message to all subscribers of the group.
        """
        group_channel = self._get_group_channel_name(group)
        shard = self._get_shard(group_channel)
        await shard.publish(group_channel, self.channel_layer.serialize(message))

    ################################################################################
    # Flush extension
    ################################################################################

    async def flush(self) -> None:
        """
        Flush the layer, making it like new. It can continue to be used as if it
        was just created. This also closes connections, serving as a clean-up
        method; connections will be re-opened if you continue using this layer.
        """
        self.channels = {}
        self.groups = {}
        for shard in self._shards:
            await shard.flush()


class RedisSingleShardConnection:
    """Connection to a single Redis shard for pub/sub operations."""

    def __init__(
        self, host: ChannelDecodedRedisHost, channel_layer: RedisPubSubLoopLayer
    ):
        """Initialize connection to a Redis shard.

        Args:
            host: Redis host configuration.
            channel_layer: Parent channel layer instance.
        """
        self.host = host
        self.channel_layer = channel_layer
        self._subscribed_to: set[str] = set()
        self._lock = asyncio.Lock()
        self._redis: aioredis.Redis | None = None
        self._pubsub: PubSub | None = None
        self._receive_task: Future[Any] | None = None

    async def publish(self, channel: str, message: bytes) -> None:
        """Publish a message to a Redis channel.

        Args:
            channel: The channel to publish to.
            message: The message bytes to publish.
        """
        async with self._lock:
            self._ensure_redis()
            assert self._redis
            await self._redis.publish(channel, message)

    async def subscribe(self, channel: str) -> None:
        """Subscribe to a Redis channel.

        Args:
            channel: The channel to subscribe to.
        """
        async with self._lock:
            if channel not in self._subscribed_to:
                self._ensure_redis()
                self._ensure_receiver()
                assert self._pubsub
                await self._pubsub.subscribe(channel)
                self._subscribed_to.add(channel)

    async def unsubscribe(self, channel: str) -> None:
        """Unsubscribe from a Redis channel.

        Args:
            channel: The channel to unsubscribe from.
        """
        async with self._lock:
            if channel in self._subscribed_to:
                self._ensure_redis()
                self._ensure_receiver()
                assert self._pubsub
                await self._pubsub.unsubscribe(channel)
                self._subscribed_to.remove(channel)

    async def flush(self) -> None:
        """Clean up Redis connections and tasks."""
        async with self._lock:
            if self._receive_task is not None:
                self._receive_task.cancel()
                try:
                    await self._receive_task
                except asyncio.CancelledError:
                    pass
                self._receive_task = None
            if self._redis is not None:
                # The pool was created just for this client, so make sure it is closed,
                # otherwise it will schedule the connection to be closed inside the
                # __del__ method, which doesn't have a loop running anymore.
                await close_redis(self._redis)
                self._redis = None
                self._pubsub = None
            self._subscribed_to = set()

    async def _do_receiving(self) -> None:
        """Background task to receive messages from Redis pub/sub."""
        while True:
            try:
                if self._pubsub and self._pubsub.subscribed:
                    message = cast(
                        dict[str, Any] | None,
                        await self._pubsub.get_message(
                            ignore_subscribe_messages=True, timeout=0.1
                        ),
                    )
                    self._receive_message(message)
                else:
                    await asyncio.sleep(0.1)
            except (TimeoutError, asyncio.CancelledError, GeneratorExit):
                raise
            except BaseException:
                logger.exception("Unexpected exception in receive task")
                await asyncio.sleep(1)

    def _receive_message(self, message: dict[str, Any] | None) -> None:
        """Process a received Redis pub/sub message.

        Args:
            message: The Redis pub/sub message, or None if no message.
        """
        if message is not None:
            name = message["channel"]
            data = message["data"]
            if isinstance(name, bytes):
                name = name.decode()
            if name in self.channel_layer.channels:
                self.channel_layer.channels[name].put_nowait(data)
            elif name in self.channel_layer.groups:
                for channel_name in self.channel_layer.groups[name]:
                    if channel_name in self.channel_layer.channels:
                        self.channel_layer.channels[channel_name].put_nowait(data)

    def _ensure_redis(self) -> None:
        """Ensure Redis connection and pub/sub are initialized."""
        if self._redis is None:
            pool = create_pool(self.host)
            self._redis = aioredis.Redis(connection_pool=pool)
            self._pubsub = self._redis.pubsub()

    def _ensure_receiver(self) -> None:
        """Ensure the background receiver task is running."""
        if self._receive_task is None:
            self._receive_task = asyncio.ensure_future(self._do_receiving())
