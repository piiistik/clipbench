"""Executor that wires configuration, search, and evaluation into one run."""

from clipbench.experiment.experiment import Experiment
from clipbench.configuration.configuration import Configuration
from clipbench.core.evaluator import Evaluator

from clipbench.core.search_space import SearchSpace
from clipbench.core.registry import (
    get_registered_instance_of_command_runner,
    get_registered_instance_of_search_method,
)
from clipbench.core.command_runner.command_runner import CommandRunner
from clipbench.core.search_method.search_method import SearchMethod


class Executor:
    """Coordinate search execution for a single experiment."""

    def __init__(self, configuration: Configuration):
        """Create runner and search method instances from configuration."""
        self._command_runner: CommandRunner = get_registered_instance_of_command_runner(
            configuration.command_runner_configuration
        )
        self._search_method: SearchMethod = get_registered_instance_of_search_method(
            configuration.search_method_configuration
        )
        self._budget = configuration.budget

    def execute(self, experiment: Experiment) -> SearchSpace:
        """Run the configured search method and return the populated search space."""
        search_space = {}
        evaluator = Evaluator(experiment, self._command_runner, search_space)
        self._search_method.run(
            experiment.get_search_space_definition(),
            search_space,
            evaluator,
            self._budget,
        )

        return search_space
