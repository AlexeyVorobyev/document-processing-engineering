from typing import Callable as CallableType


from src.common.dependency_injection.dependency_container import (
    DependencyContainer,
)
from src.kdctl.application import Application

class DependencyInjector(DependencyContainer):
    TAGS = ["KDCTL"]

    application: CallableType[[], Application]
