"""Abstract interface for executing batches of experiment commands."""

from abc import ABC, abstractmethod
from typing import List


class CommandRunner(ABC):
    """Contract for components that evaluate commands and return scores."""

    @abstractmethod
    def run(self, commands: List[str]) -> List[float]:
        """Execute commands and return one numeric result per command."""
        ...
