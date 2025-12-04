from clipex.core.search_method.grid_sample import GridSearchMethod
from clipex.core.search_method.random_sample import RandomSearchMethod

from clipex.core.evaluator import Evaluator
from clipex.core.command_runner.simple_runner import SimpleRunner
from clipex.experiment_converter.experiment_provider import provide_experiment
from clipex.result_viewer.result_viewer import plot_heatmap


def main():
    print("Hello from CLI 👋")
    searched = {}

    experiment = provide_experiment("./tests/unit/experiment_converter/input.xml")
    print(experiment.get_search_space_definition())

    command_runner = SimpleRunner()
    evaluator = Evaluator(experiment, command_runner, searched)

    # grid = GridSearchMethod()
    # grid.run(experiment.get_search_space_definition(), searched, evaluator, 20)
    # print(searched)

    random = RandomSearchMethod()
    random.run(experiment.get_search_space_definition(), searched, evaluator, 20)
    print(searched)

    plot_heatmap(searched, "./result.jpg")


if __name__ == "__main__":
    main()
