import random
from typing import Optional

from clipex.core.search_method.search_method import SearchMethod
from clipex.core.search_space import VariableVector, SpaceDefinition, SearchSpace
from clipex.core.evaluator import Evaluator


class RandomSearchMethod(SearchMethod):
    """
    Uniform random sampling across the integer search space.
    """

    def __init__(
        self,
        random_seed: Optional[int] = None,
    ):
        self._generator = random.Random(random_seed)

    def run(
        self,
        space_definition: SpaceDefinition,
        search_space: SearchSpace,
        evaluator: Evaluator,
        budget: int,
    ):
        variable_vectors = []
        while len(variable_vectors) < budget:
            vector = self._generate_vector(space_definition)
            if vector not in variable_vectors:
                variable_vectors.append(vector)

        evaluator.evaluate(variable_vectors)

    def _generate_vector(self, space_definition: SpaceDefinition) -> VariableVector:
        vector = tuple(
            self._generator.randint(min, max) for min, max in space_definition
        )
        return vector
