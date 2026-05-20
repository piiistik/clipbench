from clipbench.configuration.configuration import Configuration
from clipbench.core.executor import Executor


class _FakeRunner:
    def run(self, commands):
        return [float(len(commands)) for _ in commands]


class _FakeSearchMethod:
    def __init__(self):
        self.calls = []

    def run(self, space_definition, search_space, evaluator, budget):
        self.calls.append(
            {
                "space_definition": space_definition,
                "budget": budget,
            }
        )
        evaluator.evaluate([(1, 2)])


class _FakeExperiment:
    def get_search_space_definition(self):
        return ((0, 2), (0, 3))

    def build_command(self, vector):
        return f"echo {vector[0]} {vector[1]}"


def test_executor_wires_registry_instances_and_executes(monkeypatch):
    fake_runner = _FakeRunner()
    fake_search_method = _FakeSearchMethod()

    monkeypatch.setattr(
        "clipbench.core.executor.get_registered_instance_of_command_runner",
        lambda configuration: fake_runner,
    )
    monkeypatch.setattr(
        "clipbench.core.executor.get_registered_instance_of_search_method",
        lambda configuration: fake_search_method,
    )

    configuration = Configuration(
        search_method_configuration={"name": "dummy_search"},
        command_runner_configuration={"name": "dummy_runner"},
        budget=5,
    )
    executor = Executor(configuration)

    result = executor.execute(_FakeExperiment())

    assert fake_search_method.calls == [
        {"space_definition": ((0, 2), (0, 3)), "budget": 5}
    ]
    assert result == {(1, 2): 1.0}
