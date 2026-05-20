"""Grid-based sampling search method for bounded integer spaces."""

import itertools

from clipbench.core.search_method.search_method import SearchMethod
from clipbench.core.search_space import VariableVector, SearchSpace, SpaceDefinition

from clipbench.core.evaluator import Evaluator
from clipbench.core.registry import (
    register_search_method as register_instance,
    register_search_method_configuration as register_configuration,
)


class GridSample(SearchMethod):
    """Evaluate points from an evenly distributed grid over the search space."""

    def run(
        self,
        space_definition: SpaceDefinition,
        _: SearchSpace,
        evaluator: Evaluator,
        budget: int,
    ):
        """Build grid points from budget and evaluate them in one batch."""
        grid_points = self._build_grid(space_definition, budget)

        if grid_points:
            evaluator.evaluate(grid_points)

    def _build_grid(
        self, space_definition: SpaceDefinition, budget: int
    ) -> list[VariableVector]:
        """Build a grid with roughly the requested total number of points."""
        n_vars = len(space_definition)
        if n_vars == 0:
            return []

        # Equal division of budget among dimensions
        points_per_dim = max(1, round(budget ** (1 / n_vars)))

        grid_axes = []
        for lo, hi in space_definition:
            step = max(1, (hi - lo) // max(1, points_per_dim - 1))
            values = list(range(lo, hi + 1, step))
            grid_axes.append(values)

        grid_points = list(itertools.product(*grid_axes))
        return grid_points[:budget]


@register_configuration("grid_sample")
def configuration_grid_sample() -> dict:
    """Return configuration metadata for the grid_sample search method."""

    return {}


@register_instance("grid_sample")
def factory_grid_sample(_: dict) -> GridSample:
    """Create a GridSample instance."""

    return GridSample()
