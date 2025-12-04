from typing import List

from clipex.experiment_converter.parser import parse_xml, Static, Dynamic, Parts
from clipex.experiment.experiment import Experiment
from clipex.experiment.command_builder import CommandBuilder
from clipex.experiment.variable_handler import VariableHandler
from clipex.experiment.variable.variable import Variable


def provide_experiment(xml_path: str) -> Experiment:
    command_builder = CommandBuilder()
    variables: List[Variable] = []

    parts: Parts = parse_xml(xml_path)

    for part in parts.parts:
        if isinstance(part, Static):
            command_builder.add_static_part(part.text)
        elif isinstance(part, Dynamic):
            if part.prefix:
                command_builder.add_static_part(part.prefix)

            command_builder.add_variable_placeholder()

            if part.suffix:
                command_builder.add_static_part(part.suffix)

            variables.append(part.variable)
        else:
            raise ValueError("Unknown part type")

    variable_handler = VariableHandler(variables)

    return Experiment(command_builder, variable_handler)
