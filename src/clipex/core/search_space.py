from typing import Dict, Tuple

VariableVector = Tuple[int, ...]
Evaluation = float | None
SearchSpace = Dict[VariableVector, Evaluation]
SpaceDefinition = Tuple[Tuple[int, int], ...]
