from typing import Tuple, List

VARIABLE_PLACEHOLDER = "<VAR>"


class CommandBuilder:
    _command: List[str]

    def __init__(self):
        self._command = []

    def add_static_part(self, part: str) -> "CommandBuilder":
        self._command.append(part)
        return self

    def add_variable_placeholder(self) -> "CommandBuilder":
        self._command.append(VARIABLE_PLACEHOLDER)
        return self

    def build(self, variables: Tuple[str, ...]) -> str:
        built_command = []
        variable_index = 0
        for part in self._command:
            if part == VARIABLE_PLACEHOLDER:
                print(self._command)
                built_command.append(variables[variable_index])
                variable_index += 1
            else:
                built_command.append(part)
        return " ".join(built_command)
