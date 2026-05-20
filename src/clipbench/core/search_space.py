"""Core type aliases that define the search-space data model."""

from typing import Dict, Tuple

# Coordinates of one candidate point in the search domain.
VariableVector = Tuple[int, ...]

# Objective value for a candidate, or None when not evaluated yet.
Evaluation = float | None

# Mapping from candidate vectors to their evaluation outcomes.
SearchSpace = Dict[VariableVector, Evaluation]

# Per-dimension inclusive integer bounds as (min, max) pairs.
SpaceDefinition = Tuple[Tuple[int, int], ...]
