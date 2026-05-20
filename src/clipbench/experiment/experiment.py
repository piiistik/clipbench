"""Experiment abstraction that maps variable vectors to executable commands."""

from typing import Tuple

from clipbench.experiment.command_builder import CommandBuilder
from clipbench.experiment.variable_handler import VariableHandler


class Experiment:
    """Combine variable handling and command building for one experiment."""

    _command_builder: CommandBuilder
    _variable_handler: VariableHandler

    def __init__(
        self, command_builder: CommandBuilder, variable_handler: VariableHandler
    ):
        """Create an experiment from a command builder and variable handler."""
        self._command_builder = command_builder
        self._variable_handler = variable_handler

    def get_search_space_definition(self) -> Tuple[Tuple[int, ...]]:
        """Return integer bounds that define the searchable variable space."""
        return self._variable_handler.get_int_ranges()

    def get_variable_values(self, variable_vector: Tuple[int, ...]) -> Tuple[str, ...]:
        """Translate a variable vector into command-ready string values."""
        return self._variable_handler.as_strings(variable_vector)

    def build_command(self, variable_vector: Tuple[int, ...]) -> str:
        """Build the executable command string for a variable vector."""
        variable_strings = self._variable_handler.as_strings(variable_vector)
        command = self._command_builder.build(variable_strings)
        return command
