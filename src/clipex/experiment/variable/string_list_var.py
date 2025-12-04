from typing import Tuple, List
from enum import Enum
from itertools import combinations

from clipex.experiment.variable.variable import Variable


class StringListType(Enum):
    VARIATIONS = 1
    CASCADE = 2


class StringListVar(Variable):
    _values: List[List[str]]

    def __init__(
        self, string_list: list[str], type: StringListType, variation_n: int = 0
    ):
        super().__init__()

        if type == StringListType.CASCADE:
            self._set_cascade(string_list)
        elif type == StringListType.VARIATIONS:
            self._set_variations(string_list, variation_n)
        else:
            raise ValueError("Invalid StringListType provided")

    def int_range(self) -> Tuple[int, int]:
        return (0, len(self._values) - 1)

    def as_string(self, index: int) -> str:
        return f"[{', '.join(self._values[index])}]"

    def _set_cascade(self, string_list: list[str]):
        self._values = []
        for i in range(1, len(string_list) + 1):
            self._values.append(string_list[:i])

    def _set_variations(self, string_list: list[str], variation_n: int):
        if variation_n <= 0 or variation_n > len(string_list):
            self._values = []
            return

        self._values = [list(c) for c in combinations(string_list, variation_n)]
