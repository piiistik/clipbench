import pytest

from clipbench.core.search_method.search_method import SearchMethod


def test_search_method_cannot_be_instantiated_without_run():
    class _IncompleteSearchMethod(SearchMethod):
        pass

    with pytest.raises(TypeError):
        _IncompleteSearchMethod()
