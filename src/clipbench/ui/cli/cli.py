import argparse
from pathlib import Path

from clipbench.experiment_converter.experiment_provider import provide_experiment
from clipbench.configuration_converter.configuration_provider import (
    provide_configuration,
)
from clipbench.result_converter.result_saver import save_result
from clipbench.result_viewer.result_viewer import plot_heatmap
from clipbench.core.executor import Executor


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()

    base = Path(args.path)

    experiment = provide_experiment(base / "experiment.xml")
    print(experiment.get_search_space_definition())

    configuration = provide_configuration(base / "configuration.json")
    print(configuration)

    executor = Executor(configuration)
    searched = executor.execute(experiment)

    save_result(searched, base / "result.csv")
    plot_heatmap(searched, base / "plot.jpg")


if __name__ == "__main__":
    main()
