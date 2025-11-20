from typing import Tuple, Any
from enum import Enum
from abc import ABC, abstractmethod


class VariableType(Enum):
    INTEGER = 1
    FLOAT = 2
    STRING_LIST = 3
    TOGGLEABLE_STRING = 4


class Variable(ABC):
    @abstractmethod
    def get_value_from_index(self, index: int) -> Any: ...

    @abstractmethod
    def get_string_from_index(self, index: int) -> str: ...

    @abstractmethod
    def get_index_range(self) -> Tuple[int, int]: ...
