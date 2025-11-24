from typing import List, Tuple

from clipex.experiment.experiment import Experiment
from clipex.core.search_method.search_method import SearchMethod
from clipex.core.search_method.exhaustive import Exhaustive
from clipex.core.command_runner.command_runner import CommandRunner

Variables = Tuple[int]
SearchSpace = List[Tuple[Variables, float | None]]

class Executor:
    _experiment: Experiment
    _search_method: SearchMethod
    _command_runner: CommandRunner
    _search_space: SearchSpace = []
        
    def __init__(self, experiment: Experiment):
        self._experiment = experiment
        # this will recieve configuration and will resolve which search method to use, etc.
        self._search_method = Exhaustive(experiment.get_ranges())
        self._command_runner = CommandRunner()
        
    def execute(self):
        pass