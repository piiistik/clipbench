import argparse
from pathlib import Path

from clipbench.experiment_converter.experiment_provider import provide_experiment
from clipbench.configuration_converter.configuration_provider import (
    provide_configuration,
)
from clipbench.result_converter.result_saver import save_result
from clipbench.result_converter.analysis_generator import save_analysis
from clipbench.core.executor import Executor


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()

    base = Path(args.path)

    experiment = provide_experiment(base / "experiment.xml")

    configuration = provide_configuration(base / "configuration.json")

    executor = Executor(configuration)
    searched = executor.execute(experiment)

    save_result(searched, base / "result.csv", experiment.get_variable_values)
    save_analysis(searched, base / "analysis.json", experiment)


if __name__ == "__main__":
    main()
