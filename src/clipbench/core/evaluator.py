"""Evaluator that executes experiment commands and stores objective values."""

from typing import List

from clipbench.core.search_space import VariableVector, SearchSpace
from clipbench.core.command_runner.command_runner import CommandRunner
from clipbench.experiment.experiment import Experiment


class Evaluator:
    """Evaluate variable vectors and cache their results in a search space."""

    _experiment: Experiment
    _command_runner: CommandRunner
    _space: SearchSpace

    def __init__(
        self, experiment: Experiment, command_runner: CommandRunner, space: SearchSpace
    ):
        """Create an evaluator bound to an experiment, runner, and search space."""
        self._experiment = experiment
        self._command_runner = command_runner
        self._space = space

    def evaluate(self, variable_vectors: List[VariableVector]):
        """Run commands for variable vectors and persist the returned results."""
        commands = [
            self._experiment.build_command(vector) for vector in variable_vectors
        ]
        results = self._command_runner.run(commands)

        for vector, result in zip(variable_vectors, results):
            self._space[vector] = result
