from clipbench.experiment_converter.experiment_provider import provide_experiment
from clipbench.configuration_converter.configuration_provider import provide_configuration
from clipbench.result_viewer.result_viewer import plot_heatmap

from clipbench.core.executor import Executor


def main():
    print("Hello from CLI 👋")

    experiment = provide_experiment("temp/experiment.xml")
    print(experiment.get_search_space_definition())
    
    configuration = provide_configuration("temp/configuration.json")
    print(configuration)
    
    executor = Executor(configuration)
    searched = executor.execute(experiment)

    plot_heatmap(searched, "temp/result.jpg")


if __name__ == "__main__":
    main()
