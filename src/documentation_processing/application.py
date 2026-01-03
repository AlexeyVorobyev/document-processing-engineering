from asyncio import Future
from src.common.dependency_injection.injectable import injectable
from src.common.logger.logger_mixin import LoggerMixin
from src.documentation_processing.components.database.mongo.mongo_database import (
    MongoDatabase,
)
from src.documentation_processing.settings import Settings
from src.documentation_processing.workers.workers import Workers
from src.documentation_processing.di_tag import DI_TAG


@injectable(container_tags=[DI_TAG])
class Application(LoggerMixin):
    def __init__(
        self,
        settings: Settings,
        mongo_database: MongoDatabase,
        workers: Workers,
    ) -> None:
        self.__settings = settings
        self.__mongo_database = mongo_database
        self.__workers = workers

    async def run(self) -> None:
        self._logger.info("Starting %s", self.__settings.app.app_name)
        await self.__mongo_database.run()
        self.__workers.run()

        await Future()

    async def shutdown(self) -> None:
        self._logger.info("Shutting down %s", self.__settings.app.app_name)
        self.__workers.stop()
        await self.__mongo_database.destroy()
