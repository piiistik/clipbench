from typing import Tuple

from clipex.experiment.variable.variable import Variable


class IntVar(Variable):
    def __init__(self, min: int, max: int, step: int = 1):
        super().__init__()
        self._min = min
        self._max = max
        self._step = step

    def int_range(self) -> Tuple[int, int]:
        count = ((self._max - self._min) // self._step) + 1
        return (0, count - 1)

    def as_string(self, index: int) -> str:
        lo, hi = self.int_range()
        if not (lo <= index <= hi):
            raise IndexError(f"Index out of range {self.int_range()}")

        value = self._min + index * self._step
        return str(value)
