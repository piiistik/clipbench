from clipex.experiment.line_definition import LineDefinition, LineDefinitionBuilder
from clipex.experiment.variable.int_var import IntVar
from clipex.experiment.variable.float_var import FloatVar
from clipex.experiment.variable.string_list_var import StringListVar, StringListType
from clipex.experiment.variable.toggleable_string_var import ToggleableStringVar


def test_line_definition_build_and_get_line():
    builder = LineDefinitionBuilder()
    builder.add_static_part("echo")
    variable_int = IntVar(1, 3, 1)
    builder.add_variable(variable_int)
    variable_float = FloatVar(0.0, 1.0, 0.5)
    builder.add_variable(variable_float)
    variable_str_list = StringListVar(["A", "B"], StringListType.CASCADE)
    builder.add_variable(variable_str_list)
    variable_toggle = ToggleableStringVar("OPTION")
    builder.add_variable(variable_toggle)

    line_definition = builder.build()

    line1 = line_definition.get_line((0, 0, 0, 0))
    assert line1 == "echo 1 0.0 [A]"

    line2 = line_definition.get_line((1, 1, 1, 1))
    assert line2 == "echo 2 0.5 [A, B] OPTION"
