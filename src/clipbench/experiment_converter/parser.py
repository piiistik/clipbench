from dataclasses import dataclass, field
from typing import List, Union
from xml.etree import ElementTree as ET

"""XML parser that converts experiment files into internal model objects."""

from clipbench.experiment.variable.int_var import IntVar
from clipbench.experiment.variable.float_var import FloatVar
from clipbench.experiment.variable.variable import Variable


@dataclass
class Static:
    """Static part with text content."""

    text: str = field(metadata={"xml": "text"})

    @classmethod
    def from_xml(cls, element: ET.Element) -> "Static":
        """Build a Static part from a <Static> XML element."""
        text = element.text.strip() if element.text else ""
        return cls(text=text)


@dataclass
class Dynamic:
    """Dynamic part with a variable and optional prefix/suffix."""

    variable: Variable = field(metadata={"xml": "element"})
    prefix: str = field(default="", metadata={"xml": "attribute"})
    suffix: str = field(default="", metadata={"xml": "attribute"})

    @classmethod
    def from_xml(cls, element: ET.Element) -> "Dynamic":
        """Build a Dynamic part from a <Dynamic> XML element."""
        prefix = element.attrib.get("prefix", "")
        suffix = element.attrib.get("suffix", "")

        # Parse the child variable element
        if len(element) != 1:
            raise ValueError(
                "Dynamic element must contain exactly one variable element"
            )

        var_element = element[0]
        variable = parse_variable(var_element)

        return cls(variable=variable, prefix=prefix, suffix=suffix)


def parse_variable(element: ET.Element) -> Variable:
    """Parse variable element and return appropriate Variable instance."""
    if element.tag == "Int":
        return Int.from_xml(element)
    elif element.tag == "Float":
        return Float.from_xml(element)
    else:
        raise ValueError(f"Unknown variable type: {element.tag}")


@dataclass
class Int:
    """Int variable binding."""

    min: int = field(metadata={"xml": "attribute"})
    max: int = field(metadata={"xml": "attribute"})
    step: int = field(default=1, metadata={"xml": "attribute"})

    @classmethod
    def from_xml(cls, element: ET.Element) -> IntVar:
        """Parse an <Int> element into an IntVar instance."""
        min_val = int(element.attrib["min"])
        max_val = int(element.attrib["max"])
        step = int(element.attrib.get("step", 1))
        return IntVar(min=min_val, max=max_val, step=step)


@dataclass
class Float:
    """Float variable binding."""

    min: float = field(metadata={"xml": "attribute"})
    max: float = field(metadata={"xml": "attribute"})
    accuracy: float = field(default=1e-2, metadata={"xml": "attribute"})

    @classmethod
    def from_xml(cls, element: ET.Element) -> FloatVar:
        """Parse a <Float> element into a FloatVar instance."""
        min_val = float(element.attrib["min"])
        max_val = float(element.attrib["max"])
        accuracy = float(
            element.attrib.get("step", element.attrib.get("accuracy", 1e-2))
        )
        return FloatVar(min=min_val, max=max_val, accuracy=accuracy)


@dataclass
class Parts:
    """Root element containing all parts."""

    parts: List[Union[Static, Dynamic]] = field(
        default_factory=list, metadata={"xml": "element"}
    )

    @classmethod
    def from_xml(cls, element: ET.Element) -> "Parts":
        """Parse the <Parts> root and all child part elements."""
        if element.tag != "Parts":
            raise ValueError("Root element must be 'Parts'")

        parts = []
        for child in element:
            if child.tag == "Static":
                parts.append(Static.from_xml(child))
            elif child.tag == "Dynamic":
                parts.append(Dynamic.from_xml(child))
            else:
                raise ValueError(f"Unknown element type: {child.tag}")

        return cls(parts=parts)


def parse_xml(xml_file: str) -> Parts:
    """Parse XML file and return Parts object."""
    tree = ET.parse(xml_file)
    root = tree.getroot()
    return Parts.from_xml(root)
