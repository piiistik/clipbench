from typing import Tuple

from clipex.experiment.command_builder import CommandBuilder
from clipex.experiment.variable_handler import VariableHandler


class Experiment:
    _command_builder: CommandBuilder
    _variable_handler: VariableHandler

    def __init__(
        self, command_builder: CommandBuilder, variable_handler: VariableHandler
    ):
        self._command_builder = command_builder
        self._variable_handler = variable_handler

    def get_search_space_definition(self) -> Tuple[Tuple[int, ...]]:
        return self._variable_handler.get_int_ranges()

    def build_command(self, variable_vector: Tuple[int, ...]) -> str:
        variable_strings = self._variable_handler.as_strings(variable_vector)
        command = self._command_builder.build(variable_strings)
        return command
