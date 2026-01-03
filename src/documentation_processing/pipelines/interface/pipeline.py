from abc import ABC, abstractmethod
from typing import Awaitable


class IPipeline[I, S, O](ABC):
    @abstractmethod
    def execute(self, input: I) -> Awaitable[O]: ...

    @abstractmethod
    def _convert_input_to_state(self, input: I) -> S: ...

    @abstractmethod
    def _convert_state_to_output(self, state: S) -> O: ...
