from abc import ABC, abstractmethod
from typing import Awaitable


# Deprecated
class IDestroyable(ABC):
    @abstractmethod
    def destroy(self) -> None | Awaitable[None]: ...


class IAsyncDestroyable(ABC):
    @abstractmethod
    def destroy(self) -> Awaitable[None]: ...


class ISyncDestroyable(ABC):
    @abstractmethod
    def destroy(self) -> None: ...
