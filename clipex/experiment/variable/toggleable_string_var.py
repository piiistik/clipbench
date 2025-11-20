from typing import Tuple

from clipex.experiment.variable.variable import Variable


class ToggleableStringVar(Variable):
    def __init__(self, string: str):
        super().__init__()
        self._string = string

    def get_value_from_index(self, index: int) -> str:
        if index < 0 or index > 1:
            raise IndexError("Index out of range for ToggleableStringVar")
        return self._string if index == 1 else ""

    def get_string_from_index(self, index: int) -> str:
        return self.get_value_from_index(index)

    def get_index_range(self) -> Tuple[int, int]:
        return (0, 1)
