import traceback
from functools import wraps
from typing import Any, Callable, Concatenate, Coroutine

from src.common.logger.logger_mixin import LoggerMixin


class LoggerDecorators:
    @staticmethod
    def log[**P, R, T: LoggerMixin](
        method: Callable[Concatenate[T, P], R],
    ) -> Callable[Concatenate[T, P], R]:
        @wraps(method)
        def wrapper(self: T, *args: P.args, **kwargs: P.kwargs) -> R:
            self._logger.debug(
                f"Call method {method.__name__} with args={args}, kwargs={kwargs}"
            )

            try:
                result = method(self, *args, **kwargs)
            except Exception as error:
                self._logger.debug(
                    f"Captured: {traceback.format_exception_only(error)}"
                )
                raise error

            self._logger.debug(
                f"Executed method {method.__name__} with result={result}"
            )

            return result

        return wrapper

    @staticmethod
    def alog[**P, R, T: LoggerMixin](
        method: Callable[Concatenate[T, P], Coroutine[Any, Any, R]],
    ) -> Callable[Concatenate[T, P], Coroutine[Any, Any, R]]:
        @wraps(method)
        async def wrapper(self: T, *args: P.args, **kwargs: P.kwargs) -> R:
            self._logger.debug(
                f"Call method {method.__name__} with args={args}, kwargs={kwargs}"
            )

            try:
                result = await method(self, *args, **kwargs)
            except Exception as error:
                self._logger.debug(
                    f"Captured: {traceback.format_exception_only(error)}"
                )
                raise error

            self._logger.debug(
                f"Executed method {method.__name__} with result={result}"
            )

            return result

        return wrapper
