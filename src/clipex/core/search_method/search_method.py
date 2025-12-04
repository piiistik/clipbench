from abc import ABC, abstractmethod
from clipex.core.search_space import SearchSpace, SpaceDefinition
from clipex.core.evaluator import Evaluator


class SearchMethod(ABC):
    @abstractmethod
    def run(
        self,
        space_definition: SpaceDefinition,
        search_space: SearchSpace,
        evaluator: Evaluator,
        budget: int,
    ):
        """
        Runs the search method on the given experiment within the provided budget.
        Saves searched space to the provided search_space evaluated by evaluator.
        """
        ...
