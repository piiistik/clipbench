import xml.etree.ElementTree as ET

import pytest

from clipbench.experiment.variable.float_var import FloatVar
from clipbench.experiment.variable.int_var import IntVar
from clipbench.experiment_converter.parser import (
    Dynamic,
    Float,
    Int,
    Parts,
    Static,
    parse_variable,
    parse_xml,
)


def test_static_from_xml_strips_text():
    element = ET.fromstring("<Static>   cmd   </Static>")

    result = Static.from_xml(element)

    assert result.text == "cmd"


def test_dynamic_from_xml_keeps_prefix_and_suffix():
    element = ET.fromstring(
        '<Dynamic prefix="a:" suffix=":b"><Int min="0" max="2"/></Dynamic>'
    )

    result = Dynamic.from_xml(element)

    assert result.prefix == "a:"
    assert result.suffix == ":b"
    assert isinstance(result.variable, IntVar)


def test_dynamic_from_xml_requires_single_child():
    no_child = ET.fromstring("<Dynamic/>")
    two_children = ET.fromstring(
        "<Dynamic><Int min='0' max='1'/><Int min='0' max='1'/></Dynamic>"
    )

    with pytest.raises(ValueError, match="exactly one"):
        Dynamic.from_xml(no_child)

    with pytest.raises(ValueError, match="exactly one"):
        Dynamic.from_xml(two_children)


def test_parse_variable_int_and_float():
    int_el = ET.fromstring("<Int min='1' max='5' step='2'/>")
    float_el = ET.fromstring("<Float min='0.0' max='0.2' accuracy='0.1'/>")

    parsed_int = parse_variable(int_el)
    parsed_float = parse_variable(float_el)

    assert isinstance(parsed_int, IntVar)
    assert parsed_int.int_range() == (0, 2)
    assert isinstance(parsed_float, FloatVar)
    assert parsed_float.int_range() == (0, 2)


def test_parse_variable_unknown_tag_raises():
    element = ET.fromstring("<Bool min='0' max='1'/>")

    with pytest.raises(ValueError, match="Unknown variable type"):
        parse_variable(element)


def test_float_from_xml_uses_step_before_accuracy():
    element = ET.fromstring("<Float min='0.0' max='0.1' step='0.05' accuracy='0.5'/>")

    parsed = Float.from_xml(element)

    assert parsed.int_range() == (0, 2)
    assert parsed.as_string(1) == "0.05"


def test_int_from_xml_default_step_is_one():
    element = ET.fromstring("<Int min='2' max='4'/>")

    parsed = Int.from_xml(element)

    assert parsed.int_range() == (0, 2)
    assert parsed.as_string(2) == "4"


def test_parts_from_xml_requires_parts_root():
    root = ET.fromstring("<Root/>")

    with pytest.raises(ValueError, match="Root element"):
        Parts.from_xml(root)


def test_parse_xml_reads_document(tmp_path):
    xml_path = tmp_path / "experiment.xml"
    xml_path.write_text(
        """<?xml version='1.0'?>
<Parts>
    <Static>echo</Static>
    <Dynamic prefix='x:' suffix=':y'>
        <Int min='0' max='1'/>
    </Dynamic>
</Parts>
""",
        encoding="utf-8",
    )

    parts = parse_xml(str(xml_path))

    assert len(parts.parts) == 2
    assert isinstance(parts.parts[0], Static)
    assert isinstance(parts.parts[1], Dynamic)
