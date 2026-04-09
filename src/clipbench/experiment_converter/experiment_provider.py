from typing import List

from clipbench.experiment_converter.parser import parse_xml, Static, Dynamic, Parts
from clipbench.experiment.experiment import Experiment
from clipbench.experiment.command_builder import CommandBuilder
from clipbench.experiment.variable_handler import VariableHandler
from clipbench.experiment.variable.variable import Variable


class _WrappedDynamicVariable(Variable):
    def __init__(self, variable: Variable, prefix: str, suffix: str):
        self._variable = variable
        self._prefix = prefix
        self._suffix = suffix

    def int_range(self):
        return self._variable.int_range()

    def as_string(self, index: int) -> str:
        value = self._variable.as_string(index)
        return f"{self._prefix}{value}{self._suffix}"


def provide_experiment(xml_path: str) -> Experiment:
    command_builder = CommandBuilder()
    variables: List[Variable] = []

    parts: Parts = parse_xml(xml_path)

    for part in parts.parts:
        if isinstance(part, Static):
            command_builder.add_static_part(part.text)
        elif isinstance(part, Dynamic):
            command_builder.add_variable_placeholder()
            variables.append(
                _WrappedDynamicVariable(part.variable, part.prefix, part.suffix)
            )
        else:
            raise ValueError("Unknown part type")

    variable_handler = VariableHandler(variables)

    return Experiment(command_builder, variable_handler)
