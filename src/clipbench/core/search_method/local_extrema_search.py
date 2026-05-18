from enum import Enum
import math
import bisect
from .search_method import SearchMethod
from clipbench.core.registry import (
    register_search_method as register_instance,
    register_search_method_configuration as register_configuration,
)
from clipbench.core.search_space import SpaceDefinition, VariableVector
from clipbench.core.search_space import SearchSpace
from clipbench.core.evaluator import Evaluator
from .random_sample import RandomSample
from .grid_sample import GridSample
from typing import List, Optional


class SearchTarget(Enum):
    MIN = "min"
    MAX = "max"


class LocalExtremaSearch(SearchMethod):
    def __init__(
        self,
        seed: Optional[int],
        search_target: SearchTarget,
        number_of_iterations: int = 10,
        budget_fraction_per_iteration: float = 0.1,
        spread_of_search: float = 1.0,
        localization_radius: float = 0.1,
        candidate_pool_ratio: float = 0.25,
        sampler_type: str = "random_sample",
        sampler_config: Optional[dict] = None,
    ):
        self._sampler = self._create_sampler(sampler_type, sampler_config or {}, seed)
        # Always keep a random sampler for localized sampling around candidates
        self._random_sampler = RandomSample(seed)
        self._search_target = search_target
        self._number_of_iterations = number_of_iterations
        self._budget_fraction_per_iteration = budget_fraction_per_iteration
        self._spread_of_search = spread_of_search
        self._localization_radius = localization_radius
        self._candidate_pool_ratio = max(0.01, min(1.0, candidate_pool_ratio))

    def _create_sampler(
        self, sampler_type: str, sampler_config: dict, seed: Optional[int]
    ):
        """Create appropriate sampler instance based on type."""
        if sampler_type == "random_sample":
            return RandomSample(sampler_config.get("random_seed", seed))
        elif sampler_type == "grid_sample":
            return GridSample()
        else:
            raise ValueError(f"Unknown sampler type: {sampler_type}")

    def run(
        self,
        space_definition: SpaceDefinition,
        search_space: SearchSpace,
        evaluator: Evaluator,
        budget: int,
    ):
        remaining_budget = budget

        first_budget = max(1, int(budget * self._budget_fraction_per_iteration))
        first_budget = min(first_budget, remaining_budget)
        used_budget = self._first_iteration(
            space_definition, search_space, evaluator, first_budget
        )
        remaining_budget -= used_budget

        for iteration_index in range(self._number_of_iterations):
            if remaining_budget <= 0:
                break

            iterations_left = self._number_of_iterations - iteration_index
            iter_budget = max(1, remaining_budget // iterations_left)
            candidate_limit = max(1, int(iter_budget * self._candidate_pool_ratio))
            candidates = self._select_candidates(
                search_space, max_candidates=candidate_limit
            )
            if not candidates:
                break

            used_budget = self._iteration(
                space_definition, search_space, evaluator, iter_budget, candidates
            )
            remaining_budget -= used_budget

    def _select_candidates(
        self,
        search_space: SearchSpace,
        max_candidates: Optional[int] = None,
    ) -> List[VariableVector]:
        evaluated = [(v, e) for v, e in search_space.items() if e is not None]
        reverse = self._search_target == SearchTarget.MAX
        evaluated.sort(key=lambda x: x[1], reverse=reverse)
        ordered = [v for v, _ in evaluated]
        if max_candidates is None:
            return ordered
        return ordered[: max(0, max_candidates)]

    def _first_iteration(
        self,
        space_definition: SpaceDefinition,
        search_space: SearchSpace,
        evaluator: Evaluator,
        budget: int,
    ) -> int:
        sample_budget = budget
        before = len(search_space)
        self._sampler.run(space_definition, search_space, evaluator, sample_budget)
        return max(0, len(search_space) - before)

    def _iteration(
        self,
        space_definition: SpaceDefinition,
        search_space: SearchSpace,
        evaluator: Evaluator,
        budget: int,
        candidates: List[VariableVector],
    ) -> int:
        if budget <= 0 or not candidates:
            return 0

        max_points = math.prod((hi - lo + 1) for lo, hi in space_definition)
        available = max(0, max_points - len(search_space))
        target_budget = min(budget, available)
        if target_budget <= 0:
            return 0

        n_new = min(target_budget, max(0, int(len(candidates) * self._spread_of_search)))
        new_candidates = [
            self._random_sampler._generate_vector(space_definition) for _ in range(n_new)
        ]
        all_candidates = candidates + new_candidates
        if not all_candidates:
            return 0

        # Favor top-ranked incumbents while still allowing exploration around random additions.
        rank_weights = [max(1, len(all_candidates) - rank) for rank in range(len(all_candidates))]
        cumulative_weights = []
        running = 0
        for weight in rank_weights:
            running += weight
            cumulative_weights.append(running)

        vectors_to_evaluate = []
        max_attempts = max(100, target_budget * 30)
        attempts = 0
        while len(vectors_to_evaluate) < target_budget and attempts < max_attempts:
            pick = self._random_sampler._generator.randint(1, cumulative_weights[-1])
            candidate_index = bisect.bisect_left(cumulative_weights, pick)
            candidate = all_candidates[candidate_index]
            vector = self._sample_around(candidate, space_definition)
            if vector not in search_space and vector not in vectors_to_evaluate:
                vectors_to_evaluate.append(vector)
            attempts += 1

        if vectors_to_evaluate:
            evaluator.evaluate(vectors_to_evaluate)
        return len(vectors_to_evaluate)

    def _sample_around(
        self, candidate: VariableVector, space_definition: SpaceDefinition
    ) -> VariableVector:
        vector = []
        for value, (min_val, max_val) in zip(candidate, space_definition):
            radius = int(self._localization_radius * (max_val - min_val))
            low = max(min_val, value - radius)
            high = min(max_val, value + radius)
            vector.append(self._random_sampler._generator.randint(low, high))
        return tuple(vector)

@register_instance("local_extrema_search")
def factory_local_extrema_search(configuration: dict) -> LocalExtremaSearch:
    return LocalExtremaSearch(
        seed=configuration.get("random_seed"),
        search_target=SearchTarget(configuration.get("search_target", "min")),
        number_of_iterations=configuration.get("number_of_iterations", 10),
        budget_fraction_per_iteration=configuration.get("budget_fraction_per_iteration", 0.1),
        spread_of_search=configuration.get("spread_of_search", 1.0),
        localization_radius=configuration.get("localization_radius", 0.1),
        candidate_pool_ratio=configuration.get("candidate_pool_ratio", 0.25),
        sampler_type=configuration.get("sampler_type", "random_sample"),
        sampler_config=configuration.get("sampler_config", {}),
    )


@register_configuration("local_extrema_search")
def configuration_local_extrema_search() -> dict:
    return {
        "random_seed": {
            "type": "int",
            "description": "Seed for random number generator",
            "default": None,
        },
        "search_target": {
            "type": "str",
            "description": "Optimization direction: 'min' or 'max'",
            "default": "min",
        },
        "number_of_iterations": {
            "type": "int",
            "description": "Number of search iterations",
            "default": 10,
        },
        "budget_fraction_per_iteration": {
            "type": "float",
            "description": "Fraction of budget to spend per iteration",
            "default": 0.1,
        },
        "spread_of_search": {
            "type": "float",
            "description": "Ratio of new random candidates added relative to existing candidates per iteration",
            "default": 1.0,
        },
        "localization_radius": {
            "type": "float",
            "description": "Relative radius (per dimension) within which to sample around each candidate",
            "default": 0.1,
        },
        "candidate_pool_ratio": {
            "type": "float",
            "description": "Fraction of iter_budget used as elite candidate pool size for local refinement",
            "default": 0.25,
        },
        "sampler_type": {
            "type": "str",
            "description": "Type of sampler to use for initial iteration: 'random_sample' or 'grid_sample'",
            "default": "random_sample",
        },
        "sampler_config": {
            "type": "dict",
            "description": "Configuration dictionary for the sampler (e.g., {'random_seed': 42} for random_sample)",
            "default": {},
        },
    }
