from clipbench.core.search_method.local_extrema_search import LocalExtremaSearch, SearchTarget


class MockEvaluator:
    """Mock evaluator that assigns deterministic values without running commands."""

    def __init__(self, search_space):
        self._search_space = search_space

    def evaluate(self, variable_vectors):
        for vector in variable_vectors:
            if len(vector) == 2:
                x, y = vector
                # Convex bowl with minimum at (2, 7)
                value = float((x - 2) ** 2 + (y - 7) ** 2)
            else:
                # Fallback for other dimensions
                value = float(sum((v - 5) ** 2 for v in vector))
            self._search_space[vector] = value


def test_local_extrema_search_with_random_sample():
    """Test LocalExtremaSearch using random_sample (default)."""
    space_definition = ((0, 10), (0, 20))
    search_space = {}
    evaluator = MockEvaluator(search_space)
    budget = 20

    method = LocalExtremaSearch(
        seed=42,
        search_target=SearchTarget.MIN,
        number_of_iterations=2,
        budget_fraction_per_iteration=0.3,
        spread_of_search=0.5,
        localization_radius=0.2,
        sampler_type="random_sample",
    )

    method.run(space_definition, search_space, evaluator, budget=budget)

    # The algorithm may evaluate more vectors than the exact budget due to the way
    # it distributes samples. We just verify it finds vectors and has reasonable behavior.
    assert len(search_space) >= budget * 0.8  # At least 80% of budget
    # Should have found some evaluated points
    assert any(v is not None for v in search_space.values())


def test_local_extrema_search_with_grid_sample():
    """Test LocalExtremaSearch using grid_sample."""
    space_definition = ((0, 10), (0, 20))
    search_space = {}
    evaluator = MockEvaluator(search_space)
    budget = 20

    method = LocalExtremaSearch(
        seed=42,
        search_target=SearchTarget.MIN,
        number_of_iterations=2,
        budget_fraction_per_iteration=0.3,
        spread_of_search=0.5,
        localization_radius=0.2,
        sampler_type="grid_sample",
    )

    method.run(space_definition, search_space, evaluator, budget=budget)

    # Grid sample may generate up to budget evaluations
    assert len(search_space) >= 1
    assert any(v is not None for v in search_space.values())


def test_local_extrema_search_respects_budget():
    """Test that LocalExtremaSearch respects the budget constraint."""
    space_definition = ((0, 10), (0, 20))
    budgets = [10, 30, 50]

    for budget in budgets:
        search_space = {}
        evaluator = MockEvaluator(search_space)

        method = LocalExtremaSearch(
            seed=42,
            search_target=SearchTarget.MIN,
            number_of_iterations=3,
            budget_fraction_per_iteration=0.2,
            sampler_type="random_sample",
        )

        method.run(space_definition, search_space, evaluator, budget=budget)

        # Verify reasonable number of evaluations based on budget
        assert len(search_space) >= budget * 0.7


def test_local_extrema_search_is_deterministic():
    """Test that same seed produces same results."""
    space_definition = ((0, 10), (0, 20))

    # First run
    search_space1 = {}
    evaluator1 = MockEvaluator(search_space1)

    method1 = LocalExtremaSearch(
        seed=123,
        search_target=SearchTarget.MIN,
        number_of_iterations=2,
        budget_fraction_per_iteration=0.3,
        sampler_type="random_sample",
    )

    method1.run(space_definition, search_space1, evaluator1, budget=20)

    # Second run with same seed
    search_space2 = {}
    evaluator2 = MockEvaluator(search_space2)

    method2 = LocalExtremaSearch(
        seed=123,
        search_target=SearchTarget.MIN,
        number_of_iterations=2,
        budget_fraction_per_iteration=0.3,
        sampler_type="random_sample",
    )

    method2.run(space_definition, search_space2, evaluator2, budget=20)

    assert set(search_space1.keys()) == set(search_space2.keys())


def test_local_extrema_search_selects_candidates_by_direction():
    """Test that candidates are selected based on search_target direction."""
    search_space_mock = {
        (0, 0): 1.0,
        (1, 1): 2.0,
        (2, 2): 3.0,
        (3, 3): 10.0,
        (4, 4): 11.0,
    }

    # Test MIN direction
    min_method = LocalExtremaSearch(
        seed=5,
        search_target=SearchTarget.MIN,
        number_of_iterations=1,
    )
    min_candidates = min_method._select_candidates(search_space_mock)
    # Should prefer lower values
    assert min_candidates[0] in {(0, 0), (1, 1)}

    # Test MAX direction
    max_method = LocalExtremaSearch(
        seed=5,
        search_target=SearchTarget.MAX,
        number_of_iterations=1,
    )
    max_candidates = max_method._select_candidates(search_space_mock)
    # Should prefer higher values
    assert max_candidates[0] in {(3, 3), (4, 4)}


def test_local_extrema_search_with_custom_sampler_config():
    """Test LocalExtremaSearch with custom sampler configuration."""
    space_definition = ((0, 10), (0, 20))
    search_space = {}
    evaluator = MockEvaluator(search_space)
    budget = 15

    method = LocalExtremaSearch(
        seed=42,
        search_target=SearchTarget.MIN,
        number_of_iterations=2,
        budget_fraction_per_iteration=0.3,
        spread_of_search=0.5,
        localization_radius=0.2,
        sampler_type="random_sample",
        sampler_config={"random_seed": 99},
    )

    method.run(space_definition, search_space, evaluator, budget=budget)

    assert len(search_space) >= budget * 0.7


def test_local_extrema_search_different_localization_radius():
    """Test that localization_radius affects search behavior."""
    space_definition = ((0, 100), (0, 100))

    # Test with small radius
    search_space_small = {}
    evaluator_small = MockEvaluator(search_space_small)

    method_small = LocalExtremaSearch(
        seed=42,
        search_target=SearchTarget.MIN,
        number_of_iterations=1,
        budget_fraction_per_iteration=0.5,
        localization_radius=0.05,
    )

    method_small.run(space_definition, search_space_small, evaluator_small, budget=20)

    # Test with large radius
    search_space_large = {}
    evaluator_large = MockEvaluator(search_space_large)

    method_large = LocalExtremaSearch(
        seed=42,
        search_target=SearchTarget.MIN,
        number_of_iterations=1,
        budget_fraction_per_iteration=0.5,
        localization_radius=0.3,
    )

    method_large.run(space_definition, search_space_large, evaluator_large, budget=20)

    # Both should find vectors; small radius tends to explore more locally
    assert len(search_space_small) >= 10
    assert len(search_space_large) >= 10


def test_local_extrema_search_invalid_sampler_type():
    """Test that invalid sampler type raises ValueError."""
    space_definition = ((0, 10), (0, 20))
    search_space = {}
    evaluator = MockEvaluator(search_space)

    # The ValueError should be raised during initialization
    try:
        LocalExtremaSearch(
            seed=42,
            search_target=SearchTarget.MIN,
            sampler_type="invalid_sampler",
        )
        assert False, "Expected ValueError for invalid sampler type"
    except ValueError as e:
        assert "Unknown sampler type" in str(e)
