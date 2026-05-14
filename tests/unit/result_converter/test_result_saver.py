from clipbench.result_converter.result_saver import save_result
import os


def test_save_result():
    result = {
        (0, 3): 1.1,
        (1, 4): 1.2,
        (2, 5): 1.3,
    }
    csv_file = os.path.join(os.path.dirname(__file__), "output.csv")

    save_result(result, csv_file)

    # Compare output and input CSVs
    input_csv = os.path.join(os.path.dirname(__file__), "input.csv")
    with open(input_csv, "r") as f:
        expected_content = f.read()

    with open(csv_file, "r") as f:
        actual_content = f.read()

    assert actual_content == expected_content


def test_save_result_with_value_columns():
    result = {
        (0, 3): 1.1,
        (1, 4): 1.2,
    }
    csv_file = os.path.join(os.path.dirname(__file__), "output.csv")

    def vector_to_values(vector):
        return tuple(str(v * 10) for v in vector)

    save_result(result, csv_file, vector_to_values)

    with open(csv_file, "r") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]

    assert lines[0] == "time,var_1_int,var_2_int,var_1_value,var_2_value"
    assert "1.1,0,3,0,30" in lines
    assert "1.2,1,4,10,40" in lines
