"""Plugin-style registry for search methods and command runners.

This module is the central extension point for the core execution pipeline.
Implementations register factories and configuration producers under string names,
and runtime configuration selects the concrete implementation by name. This keeps
the executor decoupled from implementation modules while allowing new components
to be added through registration decorators instead of hard-coded branching.

Two kinds of entries are stored:
- Factories: build runtime instances from a configuration dictionary.
- Configuration producers: return default or schema-like configuration payloads
    used by tooling and UI layers.
"""

from typing import Callable, TypeAlias

Factory: TypeAlias = Callable[[dict], object]
Producer: TypeAlias = Callable[[], dict]

_REGISTERED_SEARCH_METHOD_FACTORIES: dict[str, Factory] = {}
_REGISTERED_COMMAND_RUNNER_FACTORIES: dict[str, Factory] = {}

_REGISTERED_SEARCH_METHOD_CONFIGURATIONS: dict[str, Producer] = {}
_REGISTERED_COMMAND_RUNNER_CONFIGURATIONS: dict[str, Producer] = {}


def register_search_method(name):
    """Register a search method factory under a public name."""

    def _decorator(factory):
        _REGISTERED_SEARCH_METHOD_FACTORIES[name] = factory
        return factory

    return _decorator


def register_search_method_configuration(name):
    """Register a search method configuration producer under a public name."""

    def _decorator(configuration):
        _REGISTERED_SEARCH_METHOD_CONFIGURATIONS[name] = configuration
        return configuration

    return _decorator


def register_command_runner(name):
    """Register a command runner factory under a public name."""

    def _decorator(factory):
        _REGISTERED_COMMAND_RUNNER_FACTORIES[name] = factory
        return factory

    return _decorator


def register_command_runner_configuration(name):
    """Register a command runner configuration producer under a public name."""

    def _decorator(configuration):
        _REGISTERED_COMMAND_RUNNER_CONFIGURATIONS[name] = configuration
        return configuration

    return _decorator


def get_registered_instance_of_search_method(configuration: dict):
    """Create a registered search method instance for the given configuration."""

    try:
        factory = _REGISTERED_SEARCH_METHOD_FACTORIES[configuration["name"]]
    except KeyError:
        raise LookupError(f"No search method {configuration['name']}")
    return factory(configuration)


def get_registered_instance_of_command_runner(configuration: dict):
    """Create a registered command runner instance for the given configuration."""

    try:
        factory = _REGISTERED_COMMAND_RUNNER_FACTORIES[configuration["name"]]
    except KeyError:
        raise LookupError(f"No command runner {configuration['name']}")
    return factory(configuration)


def get_search_method_configurations():
    """Return configuration payloads for all registered search methods."""

    return {
        name: producer()
        for name, producer in _REGISTERED_SEARCH_METHOD_CONFIGURATIONS.items()
    }


def get_command_runner_configurations():
    """Return configuration payloads for all registered command runners."""

    return {
        name: producer()
        for name, producer in _REGISTERED_COMMAND_RUNNER_CONFIGURATIONS.items()
    }
