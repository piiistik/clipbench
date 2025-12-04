import itertools

from clipex.core.search_method.search_method import SearchMethod
from clipex.core.search_space import VariableVector, SearchSpace, SpaceDefinition

from clipex.core.evaluator import Evaluator


class GridSearchMethod(SearchMethod):
    """
    Grid search across the integer search space.
    The grid resolution per variable is determined from the budget,
    distributing evaluation effort evenly among dimensions.
    """

    def run(
        self,
        space_definition: SpaceDefinition,
        _: SearchSpace,
        evaluator: Evaluator,
        budget: int,
    ):
        grid_points = self._build_grid(space_definition, budget)

        if grid_points:
            print(f"Evaluating {len(grid_points)} grid points {grid_points}")
            evaluator.evaluate(grid_points)

    def _build_grid(
        self, space_definition: SpaceDefinition, budget: int
    ) -> list[VariableVector]:
        """Builds a simple grid with roughly budget points total."""
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
