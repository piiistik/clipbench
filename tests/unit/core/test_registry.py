from clipbench.core import registry


def test_register_and_get_search_method_instance():
    original = dict(registry._REGISTERED_SEARCH_METHOD_FACTORIES)
    try:
        registry._REGISTERED_SEARCH_METHOD_FACTORIES.clear()

        @registry.register_search_method("dummy_search")
        def _factory(configuration):
            return {"kind": "search", "configuration": configuration}

        result = registry.get_registered_instance_of_search_method(
            {"name": "dummy_search", "x": 1}
        )

        assert result["kind"] == "search"
        assert result["configuration"]["x"] == 1
    finally:
        registry._REGISTERED_SEARCH_METHOD_FACTORIES.clear()
        registry._REGISTERED_SEARCH_METHOD_FACTORIES.update(original)


def test_register_and_get_command_runner_instance():
    original = dict(registry._REGISTERED_COMMAND_RUNNER_FACTORIES)
    try:
        registry._REGISTERED_COMMAND_RUNNER_FACTORIES.clear()

        @registry.register_command_runner("dummy_runner")
        def _factory(configuration):
            return {"kind": "runner", "configuration": configuration}

        result = registry.get_registered_instance_of_command_runner(
            {"name": "dummy_runner", "y": 2}
        )

        assert result["kind"] == "runner"
        assert result["configuration"]["y"] == 2
    finally:
        registry._REGISTERED_COMMAND_RUNNER_FACTORIES.clear()
        registry._REGISTERED_COMMAND_RUNNER_FACTORIES.update(original)


def test_missing_search_method_raises_lookup_error():
    original = dict(registry._REGISTERED_SEARCH_METHOD_FACTORIES)
    try:
        registry._REGISTERED_SEARCH_METHOD_FACTORIES.clear()

        try:
            registry.get_registered_instance_of_search_method({"name": "missing"})
            assert False, "Expected LookupError"
        except LookupError as exc:
            assert "No search method" in str(exc)
    finally:
        registry._REGISTERED_SEARCH_METHOD_FACTORIES.clear()
        registry._REGISTERED_SEARCH_METHOD_FACTORIES.update(original)


def test_missing_command_runner_raises_lookup_error():
    original = dict(registry._REGISTERED_COMMAND_RUNNER_FACTORIES)
    try:
        registry._REGISTERED_COMMAND_RUNNER_FACTORIES.clear()

        try:
            registry.get_registered_instance_of_command_runner({"name": "missing"})
            assert False, "Expected LookupError"
        except LookupError as exc:
            assert "No command runner" in str(exc)
    finally:
        registry._REGISTERED_COMMAND_RUNNER_FACTORIES.clear()
        registry._REGISTERED_COMMAND_RUNNER_FACTORIES.update(original)


def test_configuration_producer_registration_and_aggregation():
    original_search = dict(registry._REGISTERED_SEARCH_METHOD_CONFIGURATIONS)
    original_runner = dict(registry._REGISTERED_COMMAND_RUNNER_CONFIGURATIONS)
    try:
        registry._REGISTERED_SEARCH_METHOD_CONFIGURATIONS.clear()
        registry._REGISTERED_COMMAND_RUNNER_CONFIGURATIONS.clear()

        @registry.register_search_method_configuration("search_a")
        def _search_configuration():
            return {"alpha": 1}

        @registry.register_command_runner_configuration("runner_a")
        def _runner_configuration():
            return {"beta": 2}

        assert registry.get_search_method_configurations() == {"search_a": {"alpha": 1}}
        assert registry.get_command_runner_configurations() == {"runner_a": {"beta": 2}}
    finally:
        registry._REGISTERED_SEARCH_METHOD_CONFIGURATIONS.clear()
        registry._REGISTERED_SEARCH_METHOD_CONFIGURATIONS.update(original_search)
        registry._REGISTERED_COMMAND_RUNNER_CONFIGURATIONS.clear()
        registry._REGISTERED_COMMAND_RUNNER_CONFIGURATIONS.update(original_runner)
