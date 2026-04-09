from clipbench.core.search_method.random_sample import RandomSample
from clipbench.experiment.experiment import Experiment
from clipbench.core.evaluator import Evaluator
from clipbench.experiment.command_builder import CommandBuilder
from clipbench.experiment.variable_handler import VariableHandler
from clipbench.experiment.variable.int_var import IntVar
from clipbench.core.command_runner.simple_runner import SimpleRunner


def test_random_sample():
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

    random_method = RandomSample(None)

    random_method.run(
        experiment.get_search_space_definition(), search_space, evaluator, budget=budget
    )

    assert len(search_space) == 10
