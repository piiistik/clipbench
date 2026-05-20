"""Helpers for converting variable definitions into ranges and command values."""

from typing import Tuple, List

from clipbench.experiment.variable.variable import Variable


class VariableHandler:
    """Manage experiment variables and their index-based conversions."""

    _variables: List[Variable]

    def __init__(self, variables: List[Variable] = None):
        """Store an ordered variable list, defaulting to an empty collection."""
        self._variables = variables if variables is not None else []

    def get_int_ranges(self) -> Tuple[Tuple[int, int], ...]:
        """Return per-variable integer index bounds."""
        return tuple(var.int_range() for var in self._variables)

    def as_strings(self, indices: Tuple[int, ...]) -> Tuple[str, ...]:
        """Convert variable indices into their string values in variable order."""
        if len(indices) != len(self._variables):
            raise ValueError("Length of indices must match number of variables")

        return tuple(
            var.as_string(index) for var, index in zip(self._variables, indices)
        )
