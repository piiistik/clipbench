from typing import List

from clipex.core.search_space import VariableVector, SearchSpace
from clipex.core.command_runner.command_runner import CommandRunner
from clipex.experiment.experiment import Experiment


class Evaluator:
    _experiment: Experiment
    _command_runner: CommandRunner
    _space: SearchSpace

    def __init__(
        self, experiment: Experiment, command_runner: CommandRunner, space: SearchSpace
    ):
        self._experiment = experiment
        self._command_runner = command_runner
        self._space = space

    def evaluate(self, variable_vectors: List[VariableVector]):
        """Evaluate a list of variable vectors within a given search space.

        Args:
            variable_vectors (List[VariableVector]): _description_
            space (SearchSpace): _description_
        """
        # TODO this depends on order of results from command runner to be same as inputed commands
        commands = [
            self._experiment.build_command(vector) for vector in variable_vectors
        ]
        results = self._command_runner.run(commands)

        for vector, result in zip(variable_vectors, results):
            self._space[vector] = result
