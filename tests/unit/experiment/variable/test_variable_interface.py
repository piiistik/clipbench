import pytest

from clipbench.experiment.variable.variable import Variable


def test_variable_cannot_be_instantiated_without_abstract_methods():
    class _IncompleteVariable(Variable):
        pass

    with pytest.raises(TypeError):
        _IncompleteVariable()
