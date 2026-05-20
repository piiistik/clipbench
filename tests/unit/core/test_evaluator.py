from clipbench.core.evaluator import Evaluator


class _FakeExperiment:
    def __init__(self):
        self.received_vectors = []

    def build_command(self, vector):
        self.received_vectors.append(vector)
        return f"cmd {' '.join(str(v) for v in vector)}"


class _FakeRunner:
    def __init__(self, results):
        self.results = results
        self.received_commands = None

    def run(self, commands):
        self.received_commands = list(commands)
        return list(self.results)


def test_evaluate_builds_commands_and_calls_runner():
    experiment = _FakeExperiment()
    runner = _FakeRunner([1.1, 2.2])
    space = {}
    evaluator = Evaluator(experiment, runner, space)

    evaluator.evaluate([(1, 2), (3, 4)])

    assert experiment.received_vectors == [(1, 2), (3, 4)]
    assert runner.received_commands == ["cmd 1 2", "cmd 3 4"]
    assert space == {(1, 2): 1.1, (3, 4): 2.2}


def test_evaluate_uses_zip_semantics_when_runner_returns_fewer_results():
    experiment = _FakeExperiment()
    runner = _FakeRunner([9.9])
    space = {}
    evaluator = Evaluator(experiment, runner, space)

    evaluator.evaluate([(0,), (1,)])

    assert space == {(0,): 9.9}


def test_multiple_evaluations_update_same_search_space():
    experiment = _FakeExperiment()
    runner = _FakeRunner([1.0])
    space = {}
    evaluator = Evaluator(experiment, runner, space)

    evaluator.evaluate([(0,)])
    runner.results = [2.0]
    evaluator.evaluate([(1,)])

    assert space == {(0,): 1.0, (1,): 2.0}
