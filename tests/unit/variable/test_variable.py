from clipbench.experiment.variable.int_var import IntVar
from clipbench.experiment.variable.float_var import FloatVar


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


