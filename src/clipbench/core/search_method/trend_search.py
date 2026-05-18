import math
import itertools
from typing import Dict, List, Optional, Tuple

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
        steepness_percentile_threshold: float = 0.5,
        min_effective_distance: float = 0.02,
        fallback_strategy: str = "refine",
        refine_zone_radius: float = 0.12,
        refine_zone_sample_count: int = 4,
        sampler_type: str = "random_sample",
        sampler_config: Optional[dict] = None,
    ):
        self._sampler = self._create_sampler(sampler_type, sampler_config or {}, seed)
        self._fallback_sampler = RandomSample(seed)
        self._number_of_iterations = number_of_iterations
        self._budget_fraction_initial = budget_fraction_initial
        self._k_neighbors = max(1, k_neighbors)
        self._max_neighbor_distance = max(0.0, max_neighbor_distance)
        self._max_pairs_per_iteration = max(1, max_pairs_per_iteration)
        self._steepness_percentile_threshold = max(0.0, min(1.0, steepness_percentile_threshold))
        self._min_effective_distance = max(1e-9, min_effective_distance)
        self._fallback_strategy = fallback_strategy
        self._refine_zone_radius = max(0.0, refine_zone_radius)
        self._refine_zone_sample_count = max(1, refine_zone_sample_count)

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
        evaluated = [(v, e) for v, e in search_space.items() if e is not None]

        if len(evaluated) < 2:
            self._random_fallback(space_definition, search_space, evaluator, budget)
            return

        scored_pairs = self._find_steep_pairs(evaluated, space_definition)
        candidates = self._compute_refinement_candidates(scored_pairs)
        candidates = [v for v in candidates if v not in search_space]

        if len(candidates) < budget and self._fallback_strategy == "refine":
            guided = self._refine_steep_zones(
                scored_pairs,
                space_definition,
                search_space,
                budget=budget - len(candidates),
            )
            candidates.extend(guided)

        if not candidates:
            self._random_fallback(space_definition, search_space, evaluator, budget)
            return

        evaluator.evaluate(candidates[:budget])

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
    ) -> List[Tuple[float, VariableVector, VariableVector]]:
        pair_by_key: Dict[Tuple[int, int], Tuple[float, VariableVector, VariableVector]] = {}
        per_point_edges: Dict[int, List[Tuple[float, int]]] = {
            i: [] for i in range(len(evaluated))
        }

        for i, (v1, e1) in enumerate(evaluated):
            for j in range(i + 1, len(evaluated)):
                v2, e2 = evaluated[j]
                dist = self._normalized_distance(v1, v2, space_definition)
                if dist <= 0 or dist > self._max_neighbor_distance:
                    continue
                effective_dist = max(dist, self._min_effective_distance)
                steepness = abs(e1 - e2) / effective_dist
                pair_key = (i, j)
                pair_by_key[pair_key] = (steepness, v1, v2)
                per_point_edges[i].append((steepness, j))
                per_point_edges[j].append((steepness, i))

        selected_keys = set()
        for i, edges in per_point_edges.items():
            if not edges:
                continue
            edges.sort(key=lambda x: x[0], reverse=True)
            for _, j in edges[: self._k_neighbors]:
                selected_keys.add((min(i, j), max(i, j)))

        scored_pairs = [pair_by_key[key] for key in selected_keys if key in pair_by_key]
        if not scored_pairs:
            return []

        if self._steepness_percentile_threshold > 0:
            values = [score for score, _, _ in scored_pairs]
            threshold = self._percentile(values, self._steepness_percentile_threshold)
            filtered = [entry for entry in scored_pairs if entry[0] >= threshold]
            if filtered:
                scored_pairs = filtered

        scored_pairs.sort(key=lambda x: x[0], reverse=True)
        return scored_pairs[: self._max_pairs_per_iteration]

    def _compute_refinement_candidates(
        self, scored_pairs: List[Tuple[float, VariableVector, VariableVector]]
    ) -> List[VariableVector]:
        candidates = []
        seen = set()
        for _, p, q in scored_pairs:
            mid = tuple((a + b) // 2 for a, b in zip(p, q))
            if mid != p and mid != q and mid not in seen:
                seen.add(mid)
                candidates.append(mid)
                continue

            # Midpoint collapsed to an endpoint in integer space. Try one-step
            # interior split candidates on each changing dimension.
            for d, (a, b) in enumerate(zip(p, q)):
                if a == b:
                    continue
                step = 1 if b > a else -1
                c1 = list(p)
                c1[d] = a + step
                v1 = tuple(c1)
                c2 = list(q)
                c2[d] = b - step
                v2 = tuple(c2)

                if v1 != p and v1 != q and v1 not in seen:
                    seen.add(v1)
                    candidates.append(v1)
                if v2 != p and v2 != q and v2 not in seen:
                    seen.add(v2)
                    candidates.append(v2)

        return candidates

    def _refine_steep_zones(
        self,
        scored_pairs: List[Tuple[float, VariableVector, VariableVector]],
        space_definition: SpaceDefinition,
        search_space: SearchSpace,
        budget: int,
    ) -> List[VariableVector]:
        if budget <= 0 or not scored_pairs:
            return []

        vectors = []
        seen = set()
        zone_count = min(len(scored_pairs), self._max_pairs_per_iteration)
        zones = scored_pairs[:zone_count]

        for idx, (_, p, q) in enumerate(zones):
            if len(vectors) >= budget:
                break

            anchors = [p, q, tuple((a + b) // 2 for a, b in zip(p, q))]
            radius_by_dim = []
            for lo, hi in space_definition:
                span = hi - lo
                radius_by_dim.append(max(1, int(span * self._refine_zone_radius)))

            for sample_index in range(self._refine_zone_sample_count):
                if len(vectors) >= budget:
                    break
                base = anchors[(idx + sample_index) % len(anchors)]
                candidate = []
                for value, radius, (lo, hi) in zip(base, radius_by_dim, space_definition):
                    low = max(lo, value - radius)
                    high = min(hi, value + radius)
                    candidate.append(self._fallback_sampler._generator.randint(low, high))
                vec = tuple(candidate)
                if vec in search_space or vec in seen:
                    continue
                seen.add(vec)
                vectors.append(vec)

        return vectors

    def _percentile(self, values: List[float], percentile: float) -> float:
        if not values:
            return 0.0
        ordered = sorted(values)
        if len(ordered) == 1:
            return ordered[0]
        percentile = max(0.0, min(1.0, percentile))
        idx = int(round((len(ordered) - 1) * percentile))
        return ordered[idx]

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
        steepness_percentile_threshold=configuration.get("steepness_percentile_threshold", 0.5),
        min_effective_distance=configuration.get("min_effective_distance", 0.02),
        fallback_strategy=configuration.get("fallback_strategy", "refine"),
        refine_zone_radius=configuration.get("refine_zone_radius", 0.12),
        refine_zone_sample_count=configuration.get("refine_zone_sample_count", 4),
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
        "steepness_percentile_threshold": {
            "type": "float",
            "description": "Percentile gate (0-1) applied to steepness scores before selecting pairs",
            "default": 0.5,
        },
        "min_effective_distance": {
            "type": "float",
            "description": "Minimum normalized distance used in steepness denominator to avoid unstable spikes",
            "default": 0.02,
        },
        "fallback_strategy": {
            "type": "str",
            "description": "Fallback strategy when bisection yields no new points: 'refine' or 'random'",
            "default": "refine",
        },
        "refine_zone_radius": {
            "type": "float",
            "description": "Relative per-dimension radius used for guided zone refinement",
            "default": 0.12,
        },
        "refine_zone_sample_count": {
            "type": "int",
            "description": "Number of guided samples generated per steep zone in fallback refinement",
            "default": 4,
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
