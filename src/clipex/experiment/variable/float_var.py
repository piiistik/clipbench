from typing import Tuple

from clipex.experiment.variable.variable import Variable


class FloatVar(Variable):
    def __init__(self, min: float, max: float, accuracy: float = 1e-2):
        super().__init__()
        self._min = min
        self._max = max
        self._accuracy = accuracy

    def int_range(self) -> Tuple[int, int]:
        count = int((self._max - self._min) / self._accuracy) + 1
        return (0, count - 1)

    def as_string(self, index: int) -> str:
        lo, hi = self.int_range()
        if not (lo <= index <= hi):
            raise IndexError(f"Index out of range {self.int_range()}")

        value = self._min + index * self._accuracy
        return f"{value:.2f}"
