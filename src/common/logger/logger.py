import os
from logging import FileHandler, Handler, StreamHandler, getLogger
from logging import Logger as StdLogger
from pathlib import Path
from types import TracebackType
from typing import Literal, Mapping, Type

from colorlog import ColoredFormatter

_DEFAULT_LOG_PATH = Path(os.path.join(os.getcwd(), "log.txt"))

_LOG_COLORS = {
    "DEBUG": "cyan",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "bold_red",
}

type Level = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Logger:
    __internal_loggers: list[StdLogger]
    __handlers: list[Handler]
    __level: Level

    def __init__(
        self,
        application_name: str,
        level: Level,
        dev_mode: bool,
    ) -> None:
        formatter = ColoredFormatter(
            f"%(log_color)s{application_name}%(reset)s - [%(name)s] - %(asctime)s - %(log_color)s%(levelname)s%(reset)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors=_LOG_COLORS,
        )

        self.__internal_loggers = []
        self.__level = level

        self.__handlers = [StreamHandler()]

        if dev_mode:
            self.__handlers.append(FileHandler(_DEFAULT_LOG_PATH))

        for handler in self.__handlers:
            handler.setLevel(self.__level)
            handler.setFormatter(formatter)

    @property
    def is_active(self) -> bool:
        return len(self.__internal_loggers) > 0

    def activate(self, name: str, clear: bool = True, off_propagate: bool = False):
        logger = getLogger(name)

        if clear:
            logger.handlers.clear()

        if off_propagate:
            logger.propagate = False

        logger.setLevel(self.__level)

        for handler in self.__handlers:
            logger.addHandler(handler)

        self.__internal_loggers.append(logger)

    @property
    def __loggers(self) -> list[StdLogger]:
        if not self.is_active:
            raise RuntimeError("Logger not activated")

        return self.__internal_loggers

    def debug(
        self,
        message: str,
        *args,
        exc_info: None
        | bool
        | tuple[Type[BaseException], BaseException, TracebackType | None]
        | tuple[None, None, None]
        | BaseException = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
    ) -> None:
        for logger in self.__loggers:
            logger.debug(
                message,
                *args,
                exc_info=exc_info,
                stacklevel=stacklevel,
                extra=extra,
                stack_info=stack_info,
            )

    def info(
        self,
        message: str,
        *args,
        exc_info: None
        | bool
        | tuple[Type[BaseException], BaseException, TracebackType | None]
        | tuple[None, None, None]
        | BaseException = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
    ) -> None:
        for logger in self.__loggers:
            logger.info(
                message,
                *args,
                exc_info=exc_info,
                stacklevel=stacklevel,
                extra=extra,
                stack_info=stack_info,
            )

    def warning(
        self,
        message: str,
        *args,
        exc_info: None
        | bool
        | tuple[Type[BaseException], BaseException, TracebackType | None]
        | tuple[None, None, None]
        | BaseException = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
    ) -> None:
        for logger in self.__loggers:
            logger.warning(
                message,
                *args,
                exc_info=exc_info,
                stacklevel=stacklevel,
                extra=extra,
                stack_info=stack_info,
            )

    def error(
        self,
        message: str,
        *args,
        exc_info: None
        | bool
        | tuple[Type[BaseException], BaseException, TracebackType | None]
        | tuple[None, None, None]
        | BaseException = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
    ) -> None:
        for logger in self.__loggers:
            logger.error(
                message,
                *args,
                exc_info=exc_info,
                stacklevel=stacklevel,
                extra=extra,
                stack_info=stack_info,
            )

    def critical(
        self,
        message: str,
        *args,
        exc_info: None
        | bool
        | tuple[Type[BaseException], BaseException, TracebackType | None]
        | tuple[None, None, None]
        | BaseException = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
    ) -> None:
        for logger in self.__loggers:
            logger.critical(
                message,
                *args,
                exc_info=exc_info,
                stacklevel=stacklevel,
                extra=extra,
                stack_info=stack_info,
            )
