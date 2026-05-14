from clipbench.core.search_method.trend_search import TrendSearch
from clipbench.experiment.experiment import Experiment
from clipbench.core.evaluator import Evaluator
from clipbench.experiment.command_builder import CommandBuilder
from clipbench.experiment.variable_handler import VariableHandler
from clipbench.experiment.variable.int_var import IntVar
from clipbench.core.command_runner.simple_runner import SimpleRunner


def _build_evaluator(var1: IntVar, var2: IntVar):
    search_space = {}
    variable_handler = VariableHandler([var1, var2])
    command_builder = (
        CommandBuilder()
        .add_static_part("")
        .add_variable_placeholder()
        .add_variable_placeholder()
    )
    experiment = Experiment(command_builder, variable_handler)
    evaluator = Evaluator(experiment, SimpleRunner(), search_space)
    return experiment, evaluator, search_space


def test_trend_search_exhausts_space_with_random_sampler_when_budget_is_larger():
    var1 = IntVar(0, 1)
    var2 = IntVar(0, 1)
    budget = 10

    experiment, evaluator, search_space = _build_evaluator(var1, var2)

    method = TrendSearch(
        seed=42,
        number_of_iterations=5,
        budget_fraction_initial=0.25,
        max_neighbor_distance=2.0,
        sampler_type="random_sample",
    )

    method.run(
        experiment.get_search_space_definition(), search_space, evaluator, budget=budget
    )

    assert len(search_space) == 4
    assert set(search_space.keys()) == {(0, 0), (0, 1), (1, 0), (1, 1)}


def test_trend_search_exhausts_space_with_grid_sampler_when_budget_is_larger():
    var1 = IntVar(0, 1)
    var2 = IntVar(0, 1)
    budget = 10

    experiment, evaluator, search_space = _build_evaluator(var1, var2)

    method = TrendSearch(
        seed=42,
        number_of_iterations=5,
        budget_fraction_initial=0.25,
        max_neighbor_distance=2.0,
        sampler_type="grid_sample",
    )

    method.run(
        experiment.get_search_space_definition(), search_space, evaluator, budget=budget
    )

    assert len(search_space) == 4
    assert set(search_space.keys()) == {(0, 0), (0, 1), (1, 0), (1, 1)}


def test_trend_search_does_not_exceed_small_budget():
    var1 = IntVar(0, 2)
    var2 = IntVar(0, 2)
    budget = 1

    experiment, evaluator, search_space = _build_evaluator(var1, var2)

    method = TrendSearch(
        seed=7,
        number_of_iterations=10,
        budget_fraction_initial=0.2,
        max_neighbor_distance=2.0,
        sampler_type="random_sample",
    )

    method.run(
        experiment.get_search_space_definition(), search_space, evaluator, budget=budget
    )

    assert len(search_space) == 1
