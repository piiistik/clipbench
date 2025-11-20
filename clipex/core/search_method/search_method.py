from abc import ABC, abstractmethod
from typing import List, Tuple

Variables = Tuple[int]
Ranges = List[Tuple[int, int]]
SearchSpace = List[Tuple[Variables, float | None]]


class SearchMethod(ABC):
    _variable_ranges: Ranges

    def __init__(self, variable_ranges: Tuple[Tuple[int, int]]):
        super().__init__()

        self._variable_ranges = variable_ranges

    @abstractmethod
    def step(self, searched: SearchSpace) -> SearchSpace: ...
