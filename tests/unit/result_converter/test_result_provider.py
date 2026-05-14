import os
from clipbench.result_converter.result_provider import provide_result


def test_result_provider():
    input_path = os.path.join(os.path.dirname(__file__), "input.csv")
    result = provide_result(input_path)
    assert result == {
        (0, 3): 1.1,
        (1, 4): 1.2,
        (2, 5): 1.3,
    }


def test_result_provider_enriched_schema(tmp_path):
    csv_path = tmp_path / "input_enriched.csv"
    csv_path.write_text(
        "\n".join(
            [
                "time,var_1_int,var_2_int,var_1_value,var_2_value",
                "1.1,0,3,0.00,3.00",
                "1.2,1,4,0.10,4.00",
                "1.3,2,5,0.20,5.00",
            ]
        ),
        encoding="utf-8",
    )

    result = provide_result(str(csv_path))
    assert result == {
        (0, 3): 1.1,
        (1, 4): 1.2,
        (2, 5): 1.3,
    }
