"""Abstract interface for experiment variables addressable by integer indices."""

from abc import ABC, abstractmethod
from typing import Tuple


class Variable(ABC):
    """Contract for variables that map integer indices to string values."""

    @property
    @abstractmethod
    def int_range(self) -> Tuple[int, int]: ...

    """Return inclusive integer index bounds as (min, max)."""

    @abstractmethod
    def as_string(self, index: int) -> str: ...

    """Convert an index within range to its command-line string value."""
