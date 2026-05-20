import pytest

from clipbench.experiment.variable.float_var import FloatVar
from clipbench.experiment.variable.int_var import IntVar
from clipbench.experiment.variable_handler import VariableHandler


def test_get_int_ranges_returns_tuple_per_variable():
    handler = VariableHandler([IntVar(0, 4, 2), FloatVar(0.0, 0.2, 0.1)])

    assert handler.get_int_ranges() == ((0, 2), (0, 2))


def test_as_strings_returns_values_in_original_variable_order():
    handler = VariableHandler([IntVar(10, 12), FloatVar(0.0, 0.2, 0.1)])

    assert handler.as_strings((1, 2)) == ("11", "0.20")


def test_as_strings_raises_on_mismatched_length():
    handler = VariableHandler([IntVar(0, 3)])

    with pytest.raises(ValueError, match="Length of indices"):
        handler.as_strings((0, 1))


def test_empty_handler_behaviour():
    handler = VariableHandler()

    assert handler.get_int_ranges() == ()
    assert handler.as_strings(()) == ()
