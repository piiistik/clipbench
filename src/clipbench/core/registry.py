from typing import Callable, TypeAlias

Factory: TypeAlias = Callable[[dict], object]
Producer: TypeAlias = Callable[[], dict]

_REGISTERED_SEARCH_METHOD_FACTORIES: dict[str, Factory] = {}
_REGISTERED_COMMAND_RUNNER_FACTORIES: dict[str, Factory] = {}

_REGISTERED_SEARCH_METHOD_CONFIGURATIONS: dict[str, Producer] = {}
_REGISTERED_COMMAND_RUNNER_CONFIGURATIONS: dict[str, Producer] = {}


def register_search_method(name):
    def _decorator(factory):
        _REGISTERED_SEARCH_METHOD_FACTORIES[name] = factory
        return factory

    return _decorator


def register_search_method_configuration(name):
    def _decorator(configuration):
        _REGISTERED_SEARCH_METHOD_CONFIGURATIONS[name] = configuration
        return configuration

    return _decorator


def register_command_runner(name):
    def _decorator(factory):
        _REGISTERED_COMMAND_RUNNER_FACTORIES[name] = factory
        return factory

    return _decorator


def register_command_runner_configuration(name):
    def _decorator(configuration):
        _REGISTERED_COMMAND_RUNNER_CONFIGURATIONS[name] = configuration
        return configuration

    return _decorator


def get_registered_instance_of_search_method(configuration: dict):
    try:
        factory = _REGISTERED_SEARCH_METHOD_FACTORIES[configuration["name"]]
    except KeyError:
        raise LookupError(f"No search method {configuration['name']}")
    return factory(configuration)


def get_registered_instance_of_command_runner(configuration: dict):
    try:
        factory = _REGISTERED_COMMAND_RUNNER_FACTORIES[configuration["name"]]
    except KeyError:
        raise LookupError(f"No command runner {configuration['name']}")
    return factory(configuration)


def get_search_method_configurations():
    return {name: producer() for name, producer in _REGISTERED_SEARCH_METHOD_CONFIGURATIONS.items()}


def get_command_runner_configurations():
    return {name: producer() for name, producer in _REGISTERED_COMMAND_RUNNER_CONFIGURATIONS.items()}
