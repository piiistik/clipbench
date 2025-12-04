from abc import ABC, abstractmethod
from typing import Tuple


class Variable(ABC):
    @property
    @abstractmethod
    def int_range(self) -> Tuple[int, int]: ...

    @abstractmethod
    def as_string(self, index: int) -> str: ...
