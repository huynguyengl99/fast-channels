from typing import Any, TypeAlias

ChannelRawRedisHost: TypeAlias = (
    dict[str, Any] | tuple[str, int] | list[str | int] | str
)

ChannelDecodedRedisHost: TypeAlias = dict[str, Any]

SymmetricEncryptionKeys: TypeAlias = list[str | bytes]
