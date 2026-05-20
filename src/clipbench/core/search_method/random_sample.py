"""Uniform random sampling search method for bounded integer spaces."""

import random
import math
from typing import Optional

from clipbench.core.search_method.search_method import SearchMethod
from clipbench.core.search_space import VariableVector, SpaceDefinition, SearchSpace
from clipbench.core.evaluator import Evaluator
from clipbench.core.registry import (
    register_search_method as register_instance,
    register_search_method_configuration as register_configuration,
)


class RandomSample(SearchMethod):
    """Sample unique variable vectors uniformly at random up to a budget."""

    def __init__(
        self,
        random_seed: Optional[int],
    ):
        """Initialize the random generator with an optional deterministic seed."""
        self._generator = random.Random(random_seed)

    def run(
        self,
        space_definition: SpaceDefinition,
        search_space: SearchSpace,
        evaluator: Evaluator,
        budget: int,
    ):
        """Generate random unique vectors and evaluate them in a single batch."""
        max_points = math.prod((hi - lo + 1) for lo, hi in space_definition)
        target_budget = min(budget, max_points)

        variable_vectors = []
        while len(variable_vectors) < target_budget:
            vector = self._generate_vector(space_definition)
            if vector not in variable_vectors:
                variable_vectors.append(vector)

        evaluator.evaluate(variable_vectors)

    def _generate_vector(self, space_definition: SpaceDefinition) -> VariableVector:
        """Generate one random vector within the provided per-dimension bounds."""
        vector = tuple(
            self._generator.randint(min, max) for min, max in space_definition
        )
        return vector


@register_instance("random_sample")
def factory_random_sample(configuration: dict) -> RandomSample:
    """Create a RandomSample instance from configuration with defaults."""

    default_seed = configuration_random_sample()["random_seed"]["default"]
    return RandomSample(configuration.get("random_seed", default_seed))


@register_configuration("random_sample")
def configuration_random_sample() -> dict:
    """Return configuration metadata for the random_sample search method."""

    return {
        "random_seed": {
            "type": "int",
            "description": "Seed for random number generator",
            "default": None,
        }
    }
