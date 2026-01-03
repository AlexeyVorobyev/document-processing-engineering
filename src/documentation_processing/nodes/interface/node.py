from abc import ABC, abstractmethod
from typing import Awaitable


class INode[T](ABC):
    @abstractmethod
    def execute(self, state: T) -> Awaitable[T]: ...
