import os
from clipex.result_converter.result_provider import provide_result


def test_result_provider():
    input_path = os.path.join(os.path.dirname(__file__), "input.csv")
    result = provide_result(input_path)
    assert result == {
        (0, 3): 1.1,
        (1, 4): 1.2,
        (2, 5): 1.3,
    }
