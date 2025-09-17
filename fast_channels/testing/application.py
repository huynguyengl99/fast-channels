"""Testing utilities for ASGI applications.

This module provides enhanced application communicators for testing
ASGI applications with proper type annotations.
"""

from typing import Any

from asgiref.testing import ApplicationCommunicator as BaseApplicationCommunicator


class ApplicationCommunicator(BaseApplicationCommunicator):
    """Enhanced ASGI application communicator with proper type annotations.

    This class extends the base ApplicationCommunicator from asgiref.testing
    to provide better type safety and documentation for testing ASGI applications.
    """

    async def send_input(self, message: Any) -> None:
        """Send a message to the ASGI application.

        Args:
            message: The message to send to the application.
        """
        return await super().send_input(message)  # type: ignore

    async def receive_output(self, timeout: float = 1) -> Any:
        """Receive output from the ASGI application.

        Args:
            timeout: Maximum time to wait for output in seconds.

        Returns:
            The message received from the application.

        Raises:
            TimeoutError: If no output is received within the timeout period.
        """
        return await super().receive_output(timeout)  # type: ignore

    async def receive_nothing(
        self, timeout: float = 0.1, interval: float = 0.01
    ) -> bool:
        """Assert that no output is received from the application.

        Args:
            timeout: Maximum time to wait for no output in seconds.
            interval: Time interval between checks in seconds.

        Returns:
            True if no output was received, False otherwise.
        """
        return await super().receive_nothing(timeout, interval)  # type: ignore

    async def wait(self, timeout: float = 1) -> None:
        """Wait for the application to finish processing.

        Args:
            timeout: Maximum time to wait in seconds.

        Raises:
            TimeoutError: If the application doesn't finish within the timeout.
        """
        return await super().wait(timeout)  # type: ignore

    def stop(self, exceptions: bool = True) -> None:
        """Stop the application communicator.

        Args:
            exceptions: Whether to raise exceptions that occurred during execution.
        """
        return super().stop(exceptions)  # type: ignore
