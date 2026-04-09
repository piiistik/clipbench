import os
from clipbench.experiment_converter.experiment_provider import provide_experiment


def test_parse_xml():

    input_path = os.path.join(os.path.dirname(__file__), "input.xml")
    experiment = provide_experiment(input_path)

    assert experiment.get_search_space_definition() == ((0, 9), (0, 3))
    assert (
        experiment.build_command([0, 0])
        == "python ./tests/interesting_functions/test_sleep_linear.py 1 1"
    )


def test_parse_xml_dynamic_prefix_suffix_no_extra_spaces(tmp_path):
    xml_path = tmp_path / "input.xml"
    xml_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<Parts>
    <Static>cmd --requirements z0:0.1 position:0.0,0.0</Static>
    <Dynamic prefix="direction:" suffix=",0.0">
        <Float min="0.0" max="0.0" accuracy="1"/>
    </Dynamic>
    <Dynamic prefix="energy:">
        <Float min="0.0" max="0.0" accuracy="1"/>
    </Dynamic>
</Parts>
""",
        encoding="utf-8",
    )

    experiment = provide_experiment(str(xml_path))
    assert (
        experiment.build_command([0, 0])
        == "cmd --requirements z0:0.1 position:0.0,0.0 direction:0.00,0.0 energy:0.00"
    )
