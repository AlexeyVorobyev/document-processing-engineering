from dependency_injector.providers import Factory

from src.common.dependency_injection.injectable import injectable
from src.common.logger.logger import Logger as CommonLogger


@injectable(provider_class=Factory, container_tags=["KDCTL"], name="logger")
class Logger(CommonLogger):
    def __init__(self) -> None:
        super().__init__(application_name="KDCTL", level="INFO", dev_mode=False)
