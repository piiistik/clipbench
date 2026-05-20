import pytest

from clipbench.core.command_runner.command_runner import CommandRunner


def test_command_runner_cannot_be_instantiated_without_run():
    class _IncompleteRunner(CommandRunner):
        pass

    with pytest.raises(TypeError):
        _IncompleteRunner()
