from abc import ABC, abstractmethod
from argparse import Namespace
from typing import Awaitable


class ICommand(ABC):
    @abstractmethod
    def execute(self, namespace: Namespace) -> Awaitable[None]: ...
