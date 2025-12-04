from clipex.experiment.variable.int_var import IntVar
from clipex.experiment.variable.float_var import FloatVar
from clipex.experiment.variable.toggleable_string_var import ToggleableStringVar
from clipex.experiment.variable.string_list_var import StringListVar, StringListType


def test_int_var():
    var = IntVar(0, 100, 2)

    assert var.int_range() == (0, 50)

    assert var.as_string(0) == "0"
    assert var.as_string(1) == "2"
    assert var.as_string(50) == "100"


def test_float_var():
    var = FloatVar(0.0, 1.0, 0.1)

    assert var.int_range() == (0, 10)

    assert var.as_string(0) == "0.00"
    assert var.as_string(1) == "0.10"
    assert var.as_string(10) == "1.00"


def test_toggleable_string_var():
    var = ToggleableStringVar("test_string")

    assert var.int_range() == (0, 1)

    assert var.as_string(0) == ""
    assert var.as_string(1) == "test_string"


def test_string_list_var_cascade():
    var = StringListVar(["a", "b", "c"], StringListType.CASCADE)

    assert var.int_range() == (0, 2)

    assert var.as_string(0) == "[a]"
    assert var.as_string(1) == "[a, b]"
    assert var.as_string(2) == "[a, b, c]"


def test_string_list_var_variations():
    var = StringListVar(["a", "b", "c"], StringListType.VARIATIONS, variation_n=2)

    assert var.int_range() == (0, 2)

    assert var.as_string(0) == "[a, b]"
    assert var.as_string(1) == "[a, c]"
    assert var.as_string(2) == "[b, c]"
