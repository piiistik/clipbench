"""Incremental builder for experiment command templates."""

from typing import Tuple, List

VARIABLE_PLACEHOLDER = "<VAR>"


class CommandBuilder:
    """Build command strings by mixing static parts and variable placeholders."""

    _command: List[str]

    def __init__(self):
        """Initialize an empty command template."""
        self._command = []

    def add_static_part(self, part: str) -> "CommandBuilder":
        """Append a literal command token to the template."""
        self._command.append(part)
        return self

    def add_variable_placeholder(self) -> "CommandBuilder":
        """Append a placeholder that will be replaced during build."""
        self._command.append(VARIABLE_PLACEHOLDER)
        return self

    def build(self, variables: Tuple[str, ...]) -> str:
        """Materialize the command by substituting placeholders in order."""
        built_command = []
        variable_index = 0
        for part in self._command:
            if part == VARIABLE_PLACEHOLDER:
                built_command.append(variables[variable_index])
                variable_index += 1
            else:
                built_command.append(part)
        return " ".join(built_command)
