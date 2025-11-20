from typing import Tuple

from clipex.experiment.variable.variable import Variable


class VariableCollection:
    def __init__(self, variables: Tuple[Variable]):
        self._variables = variables

    def get_ranges(self) -> Tuple[Tuple[int, int]]:
        return tuple(variable.get_index_range() for variable in self._variables)

    def get_values_from_indexes(self, indexes: Tuple[int]) -> Tuple[str]:
        if len(indexes) != len(self._variables):
            raise ValueError("Indexes length must match variables length")
        return tuple(
            self._variables[i].get_value_from_index(indexes[i])
            for i in range(len(self._variables))
        )

    def get_strings_from_indexes(self, indexes: Tuple[int]) -> Tuple[str]:
        if len(indexes) != len(self._variables):
            raise ValueError("Indexes length must match variables length")

        return tuple(
            self._variables[i].get_string_from_index(indexes[i])
            for i in range(len(self._variables))
        )
