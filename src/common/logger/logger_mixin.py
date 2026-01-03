from functools import cached_property
from typing import Optional

from dependency_injector.wiring import Provide, inject

from src.common.logger.logger import Logger


class LoggerMixin:
    __logger: Optional[Logger] = None

    @inject
    def __get_logger(
        self,
        logger: Logger = Provide["logger"],
    ) -> Logger:
        return logger

    @cached_property
    def _logger(self) -> Logger:
        """Получение и активация логгера приложения"""
        if self.__class__.__logger is None:
            self.__class__.__logger = self.__get_logger()
            self.__class__.__logger.activate(self.__class__.__name__)

        return self.__class__.__logger
