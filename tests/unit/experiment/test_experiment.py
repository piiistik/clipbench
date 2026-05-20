from clipbench.experiment.command_builder import CommandBuilder
from clipbench.experiment.experiment import Experiment
from clipbench.experiment.variable.int_var import IntVar
from clipbench.experiment.variable_handler import VariableHandler


def test_get_search_space_definition_delegates_to_variable_handler():
    experiment = Experiment(CommandBuilder(), VariableHandler([IntVar(3, 5)]))

    assert experiment.get_search_space_definition() == ((0, 2),)


def test_get_variable_values_delegates_to_variable_handler():
    handler = VariableHandler([IntVar(10, 12)])
    experiment = Experiment(CommandBuilder(), handler)

    assert experiment.get_variable_values((2,)) == ("12",)


def test_build_command_uses_command_builder_with_variable_values():
    command_builder = (
        CommandBuilder()
        .add_static_part("python")
        .add_static_part("app.py")
        .add_variable_placeholder()
    )
    handler = VariableHandler([IntVar(7, 9)])
    experiment = Experiment(command_builder, handler)

    assert experiment.build_command((1,)) == "python app.py 8"


def test_build_command_multiple_variables():
    command_builder = (
        CommandBuilder()
        .add_static_part("cmd")
        .add_variable_placeholder()
        .add_variable_placeholder()
    )
    handler = VariableHandler([IntVar(0, 1), IntVar(10, 11)])
    experiment = Experiment(command_builder, handler)

    assert experiment.build_command((1, 0)) == "cmd 1 10"
