from dataclasses import dataclass

from clipex.experiment.line_definition import LineDefinition


@dataclass
class Experiment:
    line_definition: LineDefinition
