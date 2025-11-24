from typing import Tuple

from clipex.experiment.line_definition import LineDefinition
from clipex.experiment.variable_collection import VariableCollection


# TODO this also has to hold search method and command runner config,
# as well as output place or smth, so we'll need some configuration file next to input xml
# config should be next to experiment definition, not in it
class Experiment:
    _variable_collection: VariableCollection
    _line_definition: LineDefinition

    def __init__(
        self,
        variable_collection: VariableCollection,
        line_definition: LineDefinition,
    ):
        self._variable_collection = variable_collection
        self._line_definition = line_definition
        
    def get_ranges(self) -> Tuple[Tuple[int, int]]:
        return self._variable_collection.get_ranges()