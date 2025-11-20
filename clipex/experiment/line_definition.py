from typing import List, Tuple

from clipex.experiment.variable.variable import Variable
from clipex.experiment.variable_collection import VariableCollection


VariableStr = str
VariableValueIndex = int


class LineDefinition:
    __line_template: List[str | VariableStr] = []
    __variable_collection: VariableCollection
    __variable_line_indexes: List[int] = []

    def __init__(
        self,
        line_template: List[str | VariableStr],
        variable_collection: VariableCollection,
        variable_line_indexes: List[int],
    ):
        self.__line_template = line_template
        self.__variable_collection = variable_collection
        self.__variable_line_indexes = variable_line_indexes

    def get_line(self, variable_value_indexes: Tuple[VariableValueIndex]) -> str:
        if len(variable_value_indexes) != len(self.__variable_line_indexes):
            raise ValueError(
                "Variable value indexes length must match variable line indexes length"
            )

        variable_strings = self.__variable_collection.get_strings_from_indexes(
            variable_value_indexes
        )

        for i, variable_line_index in enumerate(self.__variable_line_indexes):
            self.__line_template[variable_line_index] = variable_strings[i]

        return "".join(self.__line_template)

    def get_variable_ranges(self) -> Tuple[Tuple[int, int]]:
        return self.__variable_collection.get_ranges()


class LineDefinitionBuilder:
    __line_template: List[str | VariableStr] = []
    __variables: List[Variable] = []
    __variable_line_indexes: List[int] = []

    def add_static_part(self, static_part: str):
        self.__line_template.append(static_part)

    def add_variable(self, variable: Variable):
        position = len(self.__line_template)
        self.__line_template.append("")
        self.__variable_line_indexes.append(position)
        self.__variables.append(variable)

    def build(self) -> LineDefinition:
        line_definition = LineDefinition(
            self.__line_template,
            VariableCollection(tuple(self.__variables)),
            self.__variable_line_indexes,
        )
        return line_definition
