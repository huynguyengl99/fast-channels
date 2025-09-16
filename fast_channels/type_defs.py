from collections.abc import Awaitable, Callable, Iterable, Mapping, MutableMapping
from re import Pattern
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    Protocol,
    TypeAlias,
    TypedDict,
)

if TYPE_CHECKING:
    from .consumer.base import AsyncConsumer  # noqa

ChannelScope = MutableMapping[str, Any]
ChannelMessage = Mapping[str, Any]
ChannelHeaders = Iterable[tuple[bytes, bytes]]


ChannelCapacityPattern: TypeAlias = str | Pattern[str]
ChannelCapacityDict: TypeAlias = dict[ChannelCapacityPattern, int]

CompiledChannelCapacity: TypeAlias = tuple[Pattern[str], int]
CompiledChannelCapacities: TypeAlias = list[CompiledChannelCapacity]


ASGIReceiveCallable = Callable[[], Awaitable[ChannelMessage]]
ASGISendCallable = Callable[[ChannelMessage], Awaitable[None]]


class WebSocketConnectEvent(TypedDict):
    type: Literal["websocket.connect"]


class WebSocketAcceptEvent(TypedDict):
    type: Literal["websocket.accept"]
    subprotocol: str | None
    headers: ChannelHeaders


class WebSocketReceiveEvent(TypedDict):
    type: Literal["websocket.receive"]
    bytes: bytes | None
    text: str | None


class WebSocketCloseEvent(TypedDict):
    type: Literal["websocket.close"]
    code: int
    reason: str | None


class WebSocketDisconnectEvent(TypedDict):
    type: Literal["websocket.disconnect"]
    code: int
    reason: str | None


ASGI3Application = Callable[
    [
        ChannelScope,
        ASGIReceiveCallable,
        ASGISendCallable,
    ],
    Awaitable[None],
]
ASGIApplication = ASGI3Application


class ASGIApplicationProtocol(Protocol):
    consumer_class: "AsyncConsumer"

    # Accepts any initialization kwargs passed to the consumer class.
    # Typed as `Any` to allow flexibility in subclass-specific arguments.
    consumer_initkwargs: Any

    def __call__(
        self, scope: ChannelScope, receive: ASGIReceiveCallable, send: ASGISendCallable
    ) -> Awaitable[None]: ...


class MiddlewareProtocol(Protocol):
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    async def __call__(self, scope: Any, receive: Any, send: Any) -> Any: ...


ChannelApplication: TypeAlias = MiddlewareProtocol | ASGIApplication
