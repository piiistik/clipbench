from clipex.result_converter.result_saver import save_result
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
