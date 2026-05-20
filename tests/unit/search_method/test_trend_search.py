from clipbench.core.search_method.trend_search import TrendSearch


class FunctionEvaluator:
    def __init__(self, search_space, objective):
        self._search_space = search_space
        self._objective = objective

    def evaluate(self, variable_vectors):
        for vector in variable_vectors:
            self._search_space[vector] = float(self._objective(vector))


def _run(space_definition, budget, objective, **kwargs):
    search_space = {}
    evaluator = FunctionEvaluator(search_space, objective)
    method = TrendSearch(**kwargs)
    method.run(space_definition, search_space, evaluator, budget=budget)
    return search_space


def _diagonal_band_ratio(search_space, width=2):
    if not search_space:
        return 0.0
    near = sum(1 for x, y in search_space if abs(x - y) <= width)
    return near / len(search_space)


def test_trend_search_exhausts_space_with_random_sampler_when_budget_is_larger():
    search_space = _run(
        space_definition=((0, 1), (0, 1)),
        budget=10,
        objective=lambda v: v[0] + v[1],
        seed=42,
        number_of_iterations=5,
        budget_fraction_initial=0.25,
        max_neighbor_distance=2.0,
        fallback_strategy="random",
        sampler_type="random_sample",
    )

    assert len(search_space) == 4
    assert set(search_space.keys()) == {(0, 0), (0, 1), (1, 0), (1, 1)}


def test_trend_search_exhausts_space_with_grid_sampler_when_budget_is_larger():
    search_space = _run(
        space_definition=((0, 1), (0, 1)),
        budget=10,
        objective=lambda v: v[0] + v[1],
        seed=42,
        number_of_iterations=5,
        budget_fraction_initial=0.25,
        max_neighbor_distance=2.0,
        fallback_strategy="random",
        sampler_type="grid_sample",
    )

    assert len(search_space) == 4
    assert set(search_space.keys()) == {(0, 0), (0, 1), (1, 0), (1, 1)}


def test_trend_search_does_not_exceed_small_budget():
    search_space = _run(
        space_definition=((0, 2), (0, 2)),
        budget=1,
        objective=lambda v: v[0] ** 2 + v[1] ** 2,
        seed=7,
        number_of_iterations=10,
        budget_fraction_initial=0.2,
        max_neighbor_distance=2.0,
        sampler_type="random_sample",
    )
    assert len(search_space) == 1


def test_trend_search_is_deterministic_for_fixed_seed():
    kwargs = {
        "seed": 123,
        "number_of_iterations": 10,
        "budget_fraction_initial": 0.08,
        "k_neighbors": 3,
        "max_neighbor_distance": 0.5,
        "max_pairs_per_iteration": 18,
        "sampler_type": "random_sample",
    }
    objective = lambda v: 0.0 if v[0] < v[1] else 100.0
    s1 = _run(((0, 40), (0, 40)), 220, objective, **kwargs)
    s2 = _run(((0, 40), (0, 40)), 220, objective, **kwargs)

    assert set(s1.keys()) == set(s2.keys())


def test_trend_search_refine_focuses_on_transition_diagonal():
    search_space = _run(
        space_definition=((0, 40), (0, 40)),
        budget=300,
        objective=lambda v: 0.0 if v[0] < v[1] else 100.0,
        seed=42,
        number_of_iterations=12,
        budget_fraction_initial=0.08,
        k_neighbors=3,
        max_neighbor_distance=0.5,
        max_pairs_per_iteration=24,
        steepness_percentile_threshold=0.6,
        min_effective_distance=0.02,
        fallback_strategy="refine",
        refine_zone_radius=0.1,
        refine_zone_sample_count=5,
        sampler_type="random_sample",
    )

    # Uniform sampling would put about 12% of samples in this band.
    assert _diagonal_band_ratio(search_space, width=2) > 0.2


def test_trend_search_refine_is_more_focused_than_random_fallback_mode():
    common = {
        "space_definition": ((0, 40), (0, 40)),
        "budget": 280,
        "objective": lambda v: 0.0 if v[0] < v[1] else 100.0,
        "seed": 99,
        "number_of_iterations": 12,
        "budget_fraction_initial": 0.08,
        "k_neighbors": 3,
        "max_neighbor_distance": 0.5,
        "max_pairs_per_iteration": 20,
        "steepness_percentile_threshold": 0.6,
        "min_effective_distance": 0.02,
        "sampler_type": "random_sample",
    }
    refine_space = _run(
        fallback_strategy="refine",
        refine_zone_radius=0.1,
        refine_zone_sample_count=5,
        **common,
    )
    random_space = _run(fallback_strategy="random", **common)

    assert _diagonal_band_ratio(refine_space, width=2) > _diagonal_band_ratio(
        random_space, width=2
    )


def test_trend_search_midpoint_collapse_uses_guided_candidates():
    method = TrendSearch(
        seed=5,
        fallback_strategy="refine",
        refine_zone_radius=0.2,
        refine_zone_sample_count=4,
    )
    scored_pairs = [(12.0, (5, 5), (6, 5))]

    direct = method._compute_refinement_candidates(scored_pairs)
    assert direct == []

    search_space = {(5, 5): 1.0, (6, 5): 10.0}
    guided = method._refine_steep_zones(
        scored_pairs,
        space_definition=((0, 10), (0, 10)),
        search_space=search_space,
        budget=6,
    )

    assert len(guided) > 0
    for x, y in guided:
        assert 0 <= x <= 10
        assert 0 <= y <= 10
        assert (x, y) not in search_space
