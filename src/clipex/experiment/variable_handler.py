from typing import Tuple, List

from clipex.experiment.variable.variable import Variable


class VariableHandler:
    _variables: List[Variable]

    def __init__(self, variables: List[Variable] = None):
        self._variables = variables if variables is not None else []

    def get_int_ranges(self) -> Tuple[Tuple[int, int], ...]:
        return tuple(var.int_range() for var in self._variables)

    def as_strings(self, indices: Tuple[int, ...]) -> Tuple[str, ...]:
        if len(indices) != len(self._variables):
            raise ValueError("Length of indices must match number of variables")

        return tuple(
            var.as_string(index) for var, index in zip(self._variables, indices)
        )
