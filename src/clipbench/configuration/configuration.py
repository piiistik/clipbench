from dataclasses import dataclass
from typing import Any, Dict

"""Configuration data structures and builder for CLI bench runs."""


@dataclass
class Configuration:
    """Validated runtime configuration used by the application."""

    search_method_configuration: Dict[str, Any]
    command_runner_configuration: Dict[str, Any]
    budget: int


class ConfigurationBuilder:
    """Builder for creating a validated Configuration."""

    def __init__(self) -> None:
        self._search_method_configuration: Dict[str, Any]
        self._command_runner_configuration: Dict[str, Any]
        self._budget: int

    def set_search_method_configuration(
        self, config: Dict[str, Any]
    ) -> "ConfigurationBuilder":
        self._search_method_configuration = dict(config)
        return self

    def set_command_runner_configuration(
        self, config: Dict[str, Any]
    ) -> "ConfigurationBuilder":
        self._command_runner_configuration = dict(config)
        return self

    def set_budget(self, budget: int) -> "ConfigurationBuilder":
        self._budget = int(budget)
        return self

    def _validate(self) -> None:
        """Ensure all required fields are present and valid."""
        if not self._search_method_configuration:
            raise ValueError("search_method_configuration must be set and non-empty")
        if not self._command_runner_configuration:
            raise ValueError("command_runner_configuration must be set and non-empty")
        if self._budget <= 0:
            raise ValueError("budget must be > 0")

    def build(self) -> Configuration:
        self._validate()

        return Configuration(
            search_method_configuration=self._search_method_configuration,
            command_runner_configuration=self._command_runner_configuration,
            budget=self._budget,
        )
