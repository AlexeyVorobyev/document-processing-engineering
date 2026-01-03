from abc import ABC, abstractmethod
from typing import Awaitable

class IFactory[T: object](ABC):
    @abstractmethod
    def produce(self, *args, **kwargs) -> T | Awaitable[T]: ...
