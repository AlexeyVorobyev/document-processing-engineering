from abc import ABC, abstractmethod
from typing import Awaitable


# Deprecated
class IRunnable(ABC):
    @abstractmethod
    def run(self) -> None | Awaitable[None]: ...


class IAsyncRunnable(ABC):
    @abstractmethod
    def run(self) -> Awaitable[None]: ...


class ISyncRunnable(ABC):
    @abstractmethod
    def run(self) -> None: ...
