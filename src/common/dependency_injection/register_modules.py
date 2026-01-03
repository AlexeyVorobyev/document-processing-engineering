import importlib
import pkgutil
from typing import Type

from dependency_injector.containers import DeclarativeContainer

from src.common.dependency_injection.injectable import INJECTABLE_PROPERTY


def register_modules(package_name: str, container: Type[DeclarativeContainer]):
    package = importlib.import_module(package_name)

    for _, module_name, is_pkg in pkgutil.iter_modules(package.__path__):
        module_or_package_name = f"{package_name}.{module_name}"
        module = importlib.import_module(module_or_package_name)

        if is_pkg:
            register_modules(module_or_package_name, container)

        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if hasattr(attr, INJECTABLE_PROPERTY):
                attr.perform_injection(container=container)
