"""Type definitions for Redis channel layer implementation.

This module contains type aliases specific to Redis-based channel layers,
including host configuration and encryption key types.
"""

from typing import Any, TypeAlias

ChannelRawRedisHost: TypeAlias = (
    dict[str, Any] | tuple[str, int] | list[str | int] | str
)
"""Raw Redis host configuration in various supported formats.

Can be:
- str: "redis://localhost:6379"
- tuple: ("localhost", 6379)
- list: ["localhost", 6379]
- dict: {"host": "localhost", "port": 6379, "db": 0}
"""

ChannelDecodedRedisHost: TypeAlias = dict[str, Any]
"""Decoded Redis host configuration as a standardized dictionary.

Contains normalized Redis connection parameters like host, port, db, etc.
"""

SymmetricEncryptionKeys: TypeAlias = list[str | bytes]
"""List of symmetric encryption keys for message encryption.

Used for encrypting/decrypting messages in Redis channel layers.
Keys can be provided as strings or byte arrays.
"""
