from clipex.experiment.variable.float_var import FloatVar
from clipex.experiment.variable.int_var import IntVar
from clipex.experiment.variable.toggleable_string import ToggleableStringVar
from clipex.experiment.variable.string_list_var import StringListType, StringListVar

from pytest import approx


def test_float_var():
    float_var = FloatVar(0.0, 1.0, 0.2)

    index_range = float_var.get_index_range()
    assert index_range == (0, 5)

    values = [
        float_var.get_value_from_index(i)
        for i in range(index_range[0], index_range[1] + 1)
    ]
    expected_values = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    assert values == approx(expected_values, rel=1e-6)

    string_values = [
        float_var.get_string_from_index(i)
        for i in range(index_range[0], index_range[1] + 1)
    ]
    expected_string_values = [str(v) for v in expected_values]
    assert string_values == expected_string_values


def test_int_var():
    int_var = IntVar(1, 5, 1)

    index_range = int_var.get_index_range()
    assert index_range == (0, 4)

    values = [
        int_var.get_value_from_index(i)
        for i in range(index_range[0], index_range[1] + 1)
    ]
    expected_values = [1, 2, 3, 4, 5]
    assert values == expected_values

    string_values = [
        int_var.get_string_from_index(i)
        for i in range(index_range[0], index_range[1] + 1)
    ]
    expected_string_values = [str(v) for v in expected_values]
    assert string_values == expected_string_values


def test_toggleable_string_var():
    toggle_var = ToggleableStringVar("test")

    index_range = toggle_var.get_index_range()
    assert index_range == (0, 1)

    values = [
        toggle_var.get_value_from_index(i)
        for i in range(index_range[0], index_range[1] + 1)
    ]
    expected_values = ["", "test"]
    assert values == expected_values

    string_values = [
        toggle_var.get_string_from_index(i)
        for i in range(index_range[0], index_range[1] + 1)
    ]
    expected_string_values = expected_values
    assert string_values == expected_string_values


def test_string_list_var_variations():
    string_list_var = StringListVar(
        ["a", "b", "c"], StringListType.VARIATIONS, variation_n=2
    )

    index_range = string_list_var.get_index_range()
    assert index_range == (0, 2)

    values = [
        string_list_var.get_value_from_index(i)
        for i in range(index_range[0], index_range[1] + 1)
    ]
    expected_values = [["a", "b"], ["a", "c"], ["b", "c"]]
    assert values == expected_values

    string_values = [
        string_list_var.get_string_from_index(i)
        for i in range(index_range[0], index_range[1] + 1)
    ]
    expected_string_values = ["[a, b]", "[a, c]", "[b, c]"]
    assert string_values == expected_string_values


def test_string_list_var_cascade():
    string_list_var = StringListVar(["a", "b", "c"], StringListType.CASCADE)

    index_range = string_list_var.get_index_range()
    assert index_range == (0, 2)

    values = [
        string_list_var.get_value_from_index(i)
        for i in range(index_range[0], index_range[1] + 1)
    ]
    expected_values = [["a"], ["a", "b"], ["a", "b", "c"]]
    assert values == expected_values

    string_values = [
        string_list_var.get_string_from_index(i)
        for i in range(index_range[0], index_range[1] + 1)
    ]
    expected_string_values = ["[a]", "[a, b]", "[a, b, c]"]
    assert string_values == expected_string_values
