from typing import Callable as CallableType

from src.common.dependency_injection.dependency_container import (
    DependencyContainer,
)
from src.documentation_processing.application import Application
from src.documentation_processing.di_tag import DI_TAG


class DependencyInjector(DependencyContainer):
    TAGS = [DI_TAG]

    application: CallableType[[], Application]
