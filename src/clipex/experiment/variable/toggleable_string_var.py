from typing import Tuple

from clipex.experiment.variable.variable import Variable


class ToggleableStringVar(Variable):
    def __init__(self, string: str):
        super().__init__()
        self._string = string

    def int_range(self) -> Tuple[int, int]:
        return (0, 1)

    def as_string(self, index: int) -> str:
        return self._string if index == 1 else ""
