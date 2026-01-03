from dependency_injector.providers import Factory
from dependency_injector.wiring import Provide

from src.common.dependency_injection.injectable import injectable
from src.common.logger.logger import Logger as CommonLogger
from src.documentation_processing.di_tag import DI_TAG
from src.documentation_processing.settings import AppSettings


@injectable(provider_class=Factory, container_tags=[DI_TAG], name="logger")
class Logger(CommonLogger):
    def __init__(self, config: AppSettings = Provide["settings.provided.app"]) -> None:
        super().__init__(
            application_name=config.app_name,
            level=config.log_level,
            dev_mode=config.dev_mode,
        )
