from dependency_injector.containers import DeclarativeContainer

DEFAULT_CONTAINER_TAG = "DEFAULT"

class DependencyContainer(DeclarativeContainer):
    TAGS = [DEFAULT_CONTAINER_TAG]
