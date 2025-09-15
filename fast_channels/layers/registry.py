"""
Channel layer management and configuration, compatible with Django Channels.
"""

from .base import BaseChannelLayer


class ChannelLayerRegistry:
    """
    Registry pattern for managing channel layers.
    Allows direct registration of channel layer instances.
    """

    def __init__(self):
        self._layers = {}

    def register(self, alias: str, layer: BaseChannelLayer):
        """
        Register a channel layer instance with an alias.

        Args:
            alias: Name to register the layer under
            layer: Channel layer instance
        """
        self._layers[alias] = layer

    def unregister(self, alias: str):
        """
        Remove a channel layer from the registry.
        """
        if alias in self._layers:
            del self._layers[alias]

    def get(self, alias: str) -> BaseChannelLayer | None:
        """
        Get a channel layer by alias.
        """
        return self._layers.get(alias)

    def list_aliases(self) -> list[str]:
        """
        Get all registered aliases.
        """
        return list(self._layers.keys())

    def clear(self):
        """
        Clear all registered layers.
        """
        self._layers.clear()

    def __contains__(self, alias: str) -> bool:
        return alias in self._layers

    def __getitem__(self, alias: str) -> BaseChannelLayer:
        layer = self._layers.get(alias)
        if layer is None:
            raise KeyError(f"Channel layer '{alias}' not registered")
        return layer

    def __len__(self) -> int:
        return len(self._layers)


# Default global instance of the channel layer registry
channel_layers = ChannelLayerRegistry()


def get_channel_layer(alias: str) -> BaseChannelLayer | None:
    """
    Returns a channel layer by alias.
    Compatible with Django Channels get_channel_layer function.
    """
    return channel_layers.get(alias)


def register_channel_layer(alias: str, layer: BaseChannelLayer):
    """
    Register a channel layer instance.

    Example:
        layer = create_redis_channel_layer("redis://localhost:6379")
        register_channel_layer("my_layer", layer)
    """
    channel_layers.register(alias, layer)


def unregister_channel_layer(alias: str):
    """
    Remove a channel layer from the registry.
    """
    channel_layers.unregister(alias)


def list_channel_layers() -> list[str]:
    """
    Get all registered channel layer aliases.
    """
    return channel_layers.list_aliases()


def clear_channel_layers():
    """
    Clear all registered channel layers.
    """
    channel_layers.clear()
