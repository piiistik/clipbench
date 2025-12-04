import os
from clipex.experiment_converter.experiment_provider import provide_experiment


def test_parse_xml():

    input_path = os.path.join(os.path.dirname(__file__), "input.xml")
    experiment = provide_experiment(input_path)

    assert experiment.get_search_space_definition() == ((0, 9), (0, 3))
    assert (
        experiment.build_command([0, 0])
        == "python ./tests/interesting_functions/test_sleep_linear.py 1 1"
    )
