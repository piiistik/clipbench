from itertools import product
from typing import Tuple


from clipex.core.search_method.search_method import SearchMethod, SearchSpace


class Exhaustive(SearchMethod):
    def __init__(self, variable_ranges: Tuple[Tuple[int, int]]):
        super().__init__(variable_ranges)

    def step(self, _) -> SearchSpace:
        """
        Generate all permutations of variable values within the specified ranges.
        Each variable range is inclusive on both ends.

        Returns:
            SearchSpace: A list of (variables, None) tuples representing
                         all combinations of variable values.
        """
        value_ranges = [range(low, high + 1) for low, high in self._variable_ranges]

        all_combinations = product(*value_ranges)

        return [(combo, None) for combo in all_combinations]
