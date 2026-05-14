from clipbench.core.search_method.grid_sample import GridSample
from clipbench.experiment.experiment import Experiment
from clipbench.core.evaluator import Evaluator
from clipbench.experiment.command_builder import CommandBuilder
from clipbench.experiment.variable_handler import VariableHandler
from clipbench.experiment.variable.int_var import IntVar
from clipbench.core.command_runner.simple_runner import SimpleRunner


def test_grid_sample():
    var1 = IntVar(0, 10)
    var2 = IntVar(0, 20)
    budget = 10

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

    grid_method = GridSample()

    grid_method.run(
        experiment.get_search_space_definition(), search_space, evaluator, budget=budget
    )

    print(search_space)

    assert len(search_space) <= 10
    assert list(search_space.keys()) == [
        (0, 0),
        (0, 10),
        (0, 20),
        (5, 0),
        (5, 10),
        (5, 20),
        (10, 0),
        (10, 10),
        (10, 20),
    ]


def test_grid_sample_exhausts_space_when_budget_exceeds_space_size():
    var1 = IntVar(0, 1)
    var2 = IntVar(0, 1)
    budget = 10

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

    grid_method = GridSample()

    grid_method.run(
        experiment.get_search_space_definition(), search_space, evaluator, budget=budget
    )

    assert len(search_space) == 4
    assert set(search_space.keys()) == {(0, 0), (0, 1), (1, 0), (1, 1)}
