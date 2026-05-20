"""Abstract interface for budgeted search algorithms over experiment spaces."""

from abc import ABC, abstractmethod
from clipbench.core.search_space import SearchSpace, SpaceDefinition
from clipbench.core.evaluator import Evaluator


class SearchMethod(ABC):
    """Contract for search strategies that select vectors to evaluate."""

    @abstractmethod
    def run(
        self,
        space_definition: SpaceDefinition,
        search_space: SearchSpace,
        evaluator: Evaluator,
        budget: int,
    ):
        """Run the search within budget and write evaluated vectors to search_space."""
        ...
