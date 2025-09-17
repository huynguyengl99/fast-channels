"""Utility functions for fast-channels framework.

This module contains helper functions used across the fast-channels framework,
including async utilities and domain matching functions.
"""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from .type_defs import ASGIReceiveCallable


async def await_many_dispatch(
    consumer_callables: list[ASGIReceiveCallable],
    dispatch: Callable[[Any], Awaitable[None]],
) -> None:
    """
    Given a set of consumer callables, awaits on them all and passes results
    from them to the dispatch awaitable as they come in.

    Args:
        consumer_callables: List of async callables to await on.
        dispatch: Function to call with results as they come in.
    """
    # Call all callables, and ensure all return types are Futures
    tasks = [
        asyncio.ensure_future(consumer_callable())
        for consumer_callable in consumer_callables
    ]
    try:
        while True:
            # Wait for any of them to complete
            await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            # Find the completed one(s), yield results, and replace them
            for i, task in enumerate(tasks):
                if task.done():
                    result = task.result()
                    await dispatch(result)
                    tasks[i] = asyncio.ensure_future(consumer_callables[i]())
    finally:
        # Make sure we clean up tasks on exit
        for task in tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


def is_same_domain(host: str, pattern: str) -> bool:
    """
    Return ``True`` if the host is either an exact match or a match
    to the wildcard pattern.

    Any pattern beginning with a period matches a domain and all of its
    subdomains. (e.g. ``.example.com`` matches ``example.com`` and
    ``foo.example.com``). Anything else is an exact string match.

    Args:
        host: The hostname to check.
        pattern: The pattern to match against (may include wildcards).

    Returns:
        True if the host matches the pattern.
    """
    if not pattern:
        return False

    pattern = pattern.lower()
    return (
        pattern[0] == "."
        and (host.endswith(pattern) or host == pattern[1:])
        or pattern == host
    )
