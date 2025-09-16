import abc
import base64
import hashlib
import json
import random
from typing import Any

from cryptography.fernet import Fernet, MultiFernet

from .type_defs import SymmetricEncryptionKeys


class SerializerDoesNotExist(KeyError):
    """The requested serializer was not found."""


class BaseMessageSerializer(abc.ABC):
    def __init__(
        self,
        symmetric_encryption_keys: SymmetricEncryptionKeys | None = None,
        random_prefix_length: int = 0,
        expiry: int | None = None,
    ):
        self.crypter: MultiFernet | None = None

        self.random_prefix_length = random_prefix_length
        self.expiry = expiry
        # Set up any encryption objects
        self._setup_encryption(symmetric_encryption_keys)

    def _setup_encryption(
        self, symmetric_encryption_keys: SymmetricEncryptionKeys | None
    ) -> None:
        # See if we can do encryption if they asked
        if symmetric_encryption_keys:
            if isinstance(symmetric_encryption_keys, str | bytes):
                raise ValueError(
                    "symmetric_encryption_keys must be a list of possible keys"
                )
            sub_fernets: list[Fernet] = [
                self.make_fernet(key) for key in symmetric_encryption_keys
            ]
            self.crypter = MultiFernet(sub_fernets)
        else:
            self.crypter = None

    def make_fernet(self, key: str | bytes) -> Fernet:
        """
        Given a single encryption key, returns a Fernet instance using it.
        """
        if isinstance(key, str):
            key = key.encode("utf-8")
        formatted_key = base64.urlsafe_b64encode(hashlib.sha256(key).digest())
        return Fernet(formatted_key)

    @abc.abstractmethod
    def as_bytes(self, message: Any, *args: Any, **kwargs: Any) -> bytes:
        raise NotImplementedError

    @abc.abstractmethod
    def from_bytes(self, message: bytes, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    def serialize(self, raw_message: Any) -> bytes:
        """
        Serializes message to a byte string.
        """
        message = self.as_bytes(raw_message)
        if self.crypter:
            message = self.crypter.encrypt(message)

        if self.random_prefix_length > 0:
            # provide random prefix
            message = (
                random.getrandbits(8 * self.random_prefix_length).to_bytes(
                    self.random_prefix_length, "big"
                )
                + message
            )
        return message

    def deserialize(self, message: bytes) -> Any:
        """
        Deserializes from a byte string.
        """
        if self.random_prefix_length > 0:
            # Removes the random prefix
            message = message[self.random_prefix_length :]  # noqa: E203

        if self.crypter:
            ttl = self.expiry if self.expiry is None else self.expiry + 10
            message = self.crypter.decrypt(message, ttl)
        return self.from_bytes(message)


class MissingSerializer(BaseMessageSerializer):
    exception: Exception | None = None

    def __init__(self, *args: Any, **kwargs: Any):
        raise self.exception  # type: ignore[misc]


class JSONSerializer(BaseMessageSerializer):
    # json module by default always produces str while loads accepts bytes
    # thus we must force bytes conversion
    # we use UTF-8 since it is the recommended encoding for interoperability
    # see https://docs.python.org/3/library/json.html#character-encodings
    def as_bytes(self, raw_message: Any, *args: Any, **kwargs: Any) -> bytes:  # type: ignore[override]
        message = json.dumps(raw_message, *args, **kwargs)
        return message.encode("utf-8")

    from_bytes = staticmethod(json.loads)  # type: ignore[assignment]


# code ready for a future in which msgpack may become an optional dependency
try:
    import msgpack  # type: ignore[import-untyped]
except ImportError as exc:

    class MsgPackSerializer(MissingSerializer):
        exception = exc

else:

    class MsgPackSerializer(BaseMessageSerializer):  # type: ignore
        as_bytes = staticmethod(msgpack.packb)  # pyright: ignore
        from_bytes = staticmethod(msgpack.unpackb)  # pyright: ignore


class SerializersRegistry:
    """
    Serializers registry inspired by that of ``django.core.serializers``.
    """

    def __init__(self) -> None:
        self._registry: dict[str, type[BaseMessageSerializer]] = {}

    def register_serializer(
        self, format: str, serializer_class: type[BaseMessageSerializer]
    ) -> None:
        """
        Register a new serializer for given format
        """
        assert isinstance(serializer_class, type) and (
            issubclass(serializer_class, BaseMessageSerializer)
            or (
                hasattr(serializer_class, "serialize")
                and hasattr(serializer_class, "deserialize")
            )
        ), """
            `serializer_class` should be a class which implements `serialize` and `deserialize` method
            or a subclass of `channels_redis.serializers.BaseMessageSerializer`
        """

        self._registry[format] = serializer_class

    def get_serializer(
        self, format: str, *args: Any, **kwargs: Any
    ) -> BaseMessageSerializer:
        try:
            serializer_class = self._registry[format]
        except KeyError:
            raise SerializerDoesNotExist(format) from None

        return serializer_class(*args, **kwargs)


registry = SerializersRegistry()
registry.register_serializer("json", JSONSerializer)
registry.register_serializer("msgpack", MsgPackSerializer)  # type: ignore[type-abstract]
