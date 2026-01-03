import asyncio
import traceback
from abc import ABC, abstractmethod

from src.common.interfaces.runnable import ISyncRunnable
from src.common.logger.logger_mixin import LoggerMixin

_RESTART_DELAY_DEFAULT = 60  # 1 minute


class BaseAsyncioWorker(LoggerMixin, ISyncRunnable, ABC):
    _is_running: bool
    _loop: asyncio.Task | None

    def __init__(self) -> None:
        self._is_running = False
        self._loop = None

    def run(self) -> None:
        if self._is_running:
            raise RuntimeError("Worker already running")

        self._is_running = True
        self._loop = asyncio.create_task(self._worker_loop())
        self._logger.info(f"{self.__class__.__name__} started...")

    def stop(self) -> None:
        if not self._is_running:
            raise RuntimeError("Worker already stopped")

        self._is_running = False
        if self._loop:
            self._loop.cancel()

        self._logger.info(f"{self.__class__.__name__} stopped...")

    async def perform_work(self) -> None:
        await self._worker()

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def loop(self) -> asyncio.Task | None:
        return self._loop

    async def _worker_loop(self) -> None:
        while self._is_running:
            try:
                self._logger.debug("Perform work...")

                await self._worker()

                self._logger.debug(
                    f"Work performed, waiting {self._worker_interval}s..."
                )

                await asyncio.sleep(self._worker_interval)
            except Exception as error:
                self._logger.error(
                    f"Captured: {traceback.format_exception_only(error)}. Restarting..."
                )
                if not self._is_running:
                    break

                await asyncio.sleep(self._restart_delay)

    @abstractmethod
    async def _worker(self) -> None:
        raise NotImplementedError

    @property
    @abstractmethod
    def _worker_interval(self) -> int:
        raise NotImplementedError

    @property
    def _restart_delay(self) -> int:
        return _RESTART_DELAY_DEFAULT
