import pytest

from clipbench.experiment.command_builder import CommandBuilder


def test_add_methods_are_chainable():
    builder = CommandBuilder()

    assert builder.add_static_part("cmd") is builder
    assert builder.add_variable_placeholder() is builder


def test_build_empty_command_is_empty_string():
    builder = CommandBuilder()

    assert builder.build(()) == ""


def test_build_with_static_only():
    builder = CommandBuilder().add_static_part("python").add_static_part("script.py")

    assert builder.build(()) == "python script.py"


def test_build_replaces_placeholders_in_order():
    builder = (
        CommandBuilder()
        .add_static_part("cmd")
        .add_variable_placeholder()
        .add_static_part("--")
        .add_variable_placeholder()
    )

    assert builder.build(("one", "two")) == "cmd one -- two"


def test_build_raises_on_missing_variable_value():
    builder = CommandBuilder().add_variable_placeholder().add_variable_placeholder()

    with pytest.raises(IndexError):
        builder.build(("only_one",))


def test_build_ignores_extra_variable_values():
    builder = CommandBuilder().add_static_part("cmd").add_variable_placeholder()

    assert builder.build(("x", "unused")) == "cmd x"
