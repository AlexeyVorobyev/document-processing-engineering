import inspect
import re
from typing import Type, Union, get_type_hints

from dependency_injector.providers import Factory, Singleton
from dependency_injector.wiring import Provide, inject

from src.common.dependency_injection.dependency_container import (
    DEFAULT_CONTAINER_TAG,
    DependencyContainer,
)

INJECTABLE_PROPERTY = "__injectable__"


def injectable(
    name: str | None = None,
    provider_class: Type[Union[Singleton, Factory]] = Singleton,
    abstract: bool = False,
    container_tags: list[str] | None = None,
):
    """
    Warning! Doesnt work with future import annotations
    """

    def __modify_init_signature[T: Type[object]](cls: T):
        # Автоматическое применение @inject к __init__
        original_init = cls.__init__

        if not inspect.isfunction(original_init):
            return

        sig = inspect.signature(original_init)
        try:
            resolved_type_hints = get_type_hints(original_init)
        except Exception:
            resolved_type_hints = {}
        new_parameters = []
        has_provide_defaults = False

        for _, param in sig.parameters.items():
            annotation = resolved_type_hints.get(param.name, param.annotation)
            # Проверяем, есть ли Provide в аннотации
            default_value = param.default
            if annotation != inspect.Parameter.empty:
                if isinstance(param.default, Provide):  # type: ignore
                    default_value = param.default  # type: ignore
                elif inspect.isclass(annotation) and hasattr(
                    annotation, INJECTABLE_PROPERTY
                ):
                    provide_key = re.sub(
                        r"(?<!^)(?=[A-Z])", "_", annotation.__name__
                    ).lower()
                    default_value = Provide[provide_key]

            new_parameters.append(param.replace(default=default_value))

            if isinstance(default_value, Provide):  # type: ignore
                has_provide_defaults = True

        # Создаем новую сигнатуру для конструктора
        new_sig = sig.replace(parameters=new_parameters)

        positional_defaults: list[object] = []
        trailing_defaults: list[object] = []
        for param in reversed(new_parameters):
            if param.kind not in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            ):
                continue

            if param.default is inspect.Parameter.empty:
                break

            trailing_defaults.append(param.default)

        if trailing_defaults:
            positional_defaults = list(reversed(trailing_defaults))
            original_init.__defaults__ = tuple(positional_defaults)  # type: ignore[attr-defined]
        else:
            original_init.__defaults__ = None  # type: ignore[attr-defined]

        kw_defaults: dict[str, object] = {}
        for param in new_parameters:
            if (
                param.kind == inspect.Parameter.KEYWORD_ONLY
                and param.default is not inspect.Parameter.empty
            ):
                kw_defaults[param.name] = param.default

        original_init.__kwdefaults__ = kw_defaults or None  # type: ignore[attr-defined]

        if has_provide_defaults:
            patched_init = inject(original_init)
        else:
            patched_init = original_init

        patched_init.__signature__ = new_sig  # type: ignore[attr-defined]
        cls.__init__ = patched_init  # type: ignore

    def decorator[T: Type[object]](cls: T) -> T:
        __modify_init_signature(cls)

        setattr(
            cls,
            INJECTABLE_PROPERTY,
            {"name": name, "provider_class": provider_class, "abstract": abstract},
        )

        registration_name: str = (
            name or re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()
        )

        def perform_injection(
            container: Type[DependencyContainer],
        ) -> None:
            if abstract:
                return

            effective_tags = container_tags or [DEFAULT_CONTAINER_TAG]

            intersection = set(effective_tags).intersection(container.TAGS)
            if len(intersection) == 0:
                return

            # Если элемент уже есть в контейнере то не оверрайдим
            if hasattr(container, registration_name):
                return

            setattr(container, registration_name, provider_class(cls))

        setattr(cls, "perform_injection", perform_injection)

        return cls

    return decorator
