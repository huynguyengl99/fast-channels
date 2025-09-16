from typing import Any

from asgiref.testing import ApplicationCommunicator as BaseApplicationCommunicator


class ApplicationCommunicator(BaseApplicationCommunicator):
    async def send_input(self, message: Any) -> None:
        return await super().send_input(message)  # type: ignore

    async def receive_output(self, timeout: float = 1) -> Any:
        return await super().receive_output(timeout)  # type: ignore

    async def receive_nothing(
        self, timeout: float = 0.1, interval: float = 0.01
    ) -> bool:
        return await super().receive_nothing(timeout, interval)  # type: ignore

    async def wait(self, timeout: float = 1) -> None:
        return await super().wait(timeout)  # type: ignore

    def stop(self, exceptions: bool = True) -> None:
        return super().stop(exceptions)  # type: ignore
