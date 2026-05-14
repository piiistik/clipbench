import math
import itertools
from typing import List, Optional, Tuple

from clipbench.core.evaluator import Evaluator
from clipbench.core.registry import (
    register_search_method as register_instance,
    register_search_method_configuration as register_configuration,
)
from clipbench.core.search_space import SearchSpace, SpaceDefinition, VariableVector
from clipbench.core.search_method.search_method import SearchMethod
from clipbench.core.search_method.random_sample import RandomSample
from clipbench.core.search_method.grid_sample import GridSample


class TrendSearch(SearchMethod):
    """
    Bisection-based ridge finder. Prioritizes sampling between evaluated point
    pairs that have the steepest value difference relative to their distance,
    iteratively narrowing in on regions of rapid change (ridges / sharp transitions).
    """

    def __init__(
        self,
        seed: Optional[int],
        number_of_iterations: int = 10,
        budget_fraction_initial: float = 0.2,
        k_neighbors: int = 4,
        max_neighbor_distance: float = 0.3,
        max_pairs_per_iteration: int = 20,
        sampler_type: str = "random_sample",
        sampler_config: Optional[dict] = None,
    ):
        self._sampler = self._create_sampler(sampler_type, sampler_config or {}, seed)
        self._fallback_sampler = RandomSample(seed)
        self._number_of_iterations = number_of_iterations
        self._budget_fraction_initial = budget_fraction_initial
        self._k_neighbors = k_neighbors
        self._max_neighbor_distance = max_neighbor_distance
        self._max_pairs_per_iteration = max_pairs_per_iteration

    def _create_sampler(
        self, sampler_type: str, sampler_config: dict, seed: Optional[int]
    ):
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
        if budget <= 0:
            return

        max_points = math.prod((hi - lo + 1) for lo, hi in space_definition)
        target_total = min(budget, max_points)
        remaining = max(0, target_total - len(search_space))

        if remaining == 0:
            return

        initial_budget = min(max(1, int(target_total * self._budget_fraction_initial)), remaining)

        before_initial = len(search_space)
        self._sampler.run(space_definition, search_space, evaluator, initial_budget)
        remaining -= max(0, len(search_space) - before_initial)

        if remaining == 0 or self._number_of_iterations <= 0:
            return

        for i in range(self._number_of_iterations):
            if remaining <= 0:
                break

            iterations_left = self._number_of_iterations - i
            iter_budget = max(1, math.ceil(remaining / iterations_left))

            before_iteration = len(search_space)
            self._bisection_iteration(
                space_definition, search_space, evaluator, iter_budget
            )
            gained = max(0, len(search_space) - before_iteration)
            remaining -= gained

            if gained == 0:
                break

    def _bisection_iteration(
        self,
        space_definition: SpaceDefinition,
        search_space: SearchSpace,
        evaluator: Evaluator,
        budget: int,
    ):
        evaluated = [
            (v, e) for v, e in search_space.items() if e is not None
        ]

        if len(evaluated) < 2:
            # Not enough points to form pairs — fall back to random sampling
            self._random_fallback(space_definition, search_space, evaluator, budget)
            return

        pairs = self._find_steep_pairs(evaluated, space_definition)
        midpoints = self._compute_midpoints(pairs)
        midpoints = [m for m in midpoints if m not in search_space]

        if not midpoints:
            # All pairs are at integer resolution limit — fall back to random sampling
            self._random_fallback(space_definition, search_space, evaluator, budget)
            return

        evaluator.evaluate(midpoints[:budget])

    def _random_fallback(
        self,
        space_definition: SpaceDefinition,
        search_space: SearchSpace,
        evaluator: Evaluator,
        budget: int,
    ):
        """Sample random unique vectors up to budget, stopping if the space is exhausted."""
        max_points = math.prod((hi - lo + 1) for lo, hi in space_definition)
        available_points = max(0, max_points - len(search_space))
        target_budget = min(budget, available_points)

        if target_budget <= 0:
            return

        vectors = []
        max_attempts = max(100, target_budget * 20)
        attempts = 0
        while len(vectors) < target_budget and attempts < max_attempts:
            v = self._fallback_sampler._generate_vector(space_definition)
            if v not in search_space and v not in vectors:
                vectors.append(v)
            attempts += 1

        if len(vectors) < target_budget:
            for v in self._enumerate_all_vectors(space_definition):
                if v in search_space or v in vectors:
                    continue
                vectors.append(v)
                if len(vectors) >= target_budget:
                    break

        if vectors:
            evaluator.evaluate(vectors)

    def _enumerate_all_vectors(
        self, space_definition: SpaceDefinition
    ) -> List[VariableVector]:
        ranges = [range(lo, hi + 1) for lo, hi in space_definition]
        return list(itertools.product(*ranges))

    def _find_steep_pairs(
        self,
        evaluated: List[Tuple[VariableVector, float]],
        space_definition: SpaceDefinition,
    ) -> List[Tuple[VariableVector, VariableVector]]:
        scored_pairs = []
        seen_pairs = set()

        for i, (v1, e1) in enumerate(evaluated):
            # Compute distance to every other point, keep k nearest within threshold
            neighbors = []
            for j, (v2, e2) in enumerate(evaluated):
                if i == j:
                    continue
                dist = self._normalized_distance(v1, v2, space_definition)
                if dist <= self._max_neighbor_distance and dist > 0:
                    neighbors.append((dist, j, v2, e2))

            neighbors.sort(key=lambda x: x[0])

            for dist, j, v2, e2 in neighbors[: self._k_neighbors]:
                pair_key = (min(i, j), max(i, j))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)
                steepness = abs(e1 - e2) / dist
                scored_pairs.append((steepness, v1, v2))

        scored_pairs.sort(key=lambda x: x[0], reverse=True)
        return [(v1, v2) for _, v1, v2 in scored_pairs[: self._max_pairs_per_iteration]]

    def _compute_midpoints(
        self, pairs: List[Tuple[VariableVector, VariableVector]]
    ) -> List[VariableVector]:
        midpoints = []
        seen = set()
        for p, q in pairs:
            mid = tuple((a + b) // 2 for a, b in zip(p, q))
            if mid == p or mid == q:
                # Already at integer resolution limit — skip
                continue
            if mid not in seen:
                seen.add(mid)
                midpoints.append(mid)
        return midpoints

    def _normalized_distance(
        self,
        p: VariableVector,
        q: VariableVector,
        space_definition: SpaceDefinition,
    ) -> float:
        total = 0.0
        for pi, qi, (lo, hi) in zip(p, q, space_definition):
            span = hi - lo
            if span == 0:
                continue
            total += ((pi - qi) / span) ** 2
        return math.sqrt(total)


@register_instance("trend_search")
def factory_trend_search(configuration: dict) -> TrendSearch:
    return TrendSearch(
        seed=configuration.get("random_seed"),
        number_of_iterations=configuration.get("number_of_iterations", 10),
        budget_fraction_initial=configuration.get("budget_fraction_initial", 0.2),
        k_neighbors=configuration.get("k_neighbors", 4),
        max_neighbor_distance=configuration.get("max_neighbor_distance", 0.3),
        max_pairs_per_iteration=configuration.get("max_pairs_per_iteration", 20),
        sampler_type=configuration.get("sampler_type", "random_sample"),
        sampler_config=configuration.get("sampler_config", {}),
    )


@register_configuration("trend_search")
def configuration_trend_search() -> dict:
    return {
        "random_seed": {
            "type": "int",
            "description": "Seed for random number generator",
            "default": None,
        },
        "number_of_iterations": {
            "type": "int",
            "description": "Number of bisection refinement rounds",
            "default": 10,
        },
        "budget_fraction_initial": {
            "type": "float",
            "description": "Fraction of total budget spent on the initial spread sample",
            "default": 0.2,
        },
        "k_neighbors": {
            "type": "int",
            "description": "Number of nearest evaluated neighbors to pair with each point",
            "default": 4,
        },
        "max_neighbor_distance": {
            "type": "float",
            "description": "Maximum normalized distance (0-1 per dimension) to consider two points a candidate pair",
            "default": 0.3,
        },
        "max_pairs_per_iteration": {
            "type": "int",
            "description": "Maximum number of top-scored pairs to bisect per iteration",
            "default": 20,
        },
        "sampler_type": {
            "type": "str",
            "description": "Sampler used for the initial spread: 'random_sample' or 'grid_sample'",
            "default": "random_sample",
        },
        "sampler_config": {
            "type": "dict",
            "description": "Configuration dictionary passed to the initial sampler",
            "default": {},
        },
    }
