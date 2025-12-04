from abc import ABC, abstractmethod
from typing import List


# TODO maybe use somethig else then List if needed because of paralelism
class CommandRunner(ABC):
    @abstractmethod
    def run(self, commands: List[str]) -> List[float]: ...
