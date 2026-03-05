_REGISTRY = {}


def register(name):
    def _decorator(factory):
        _REGISTRY[name] = factory
        return factory

    return _decorator


def get_registered_instance(configuration: dict):
    try:
        factory = _REGISTRY[configuration["name"]]
    except KeyError:
        raise LookupError(f"No plugin {configuration["name"]}")
    return factory(configuration)
