from asyncio import sleep

from pymongo import AsyncMongoClient
from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.errors import ServerSelectionTimeoutError
from tenacity import retry, wait_fixed

from beanie import Document, init_beanie
from src.common.interfaces.destroyable import IDestroyable
from src.common.interfaces.runnable import IAsyncRunnable
from src.common.logger.logger_mixin import LoggerMixin


class MongoDatabase(LoggerMixin, IAsyncRunnable, IDestroyable):
    __url: str
    __name: str
    __model_definitions: list[type[Document]]
    __client: AsyncMongoClient

    def __init__(
        self, model_definitions: list[type[Document]], url: str, name: str
    ) -> None:
        self.__url = url
        self.__name = name
        self.__model_definitions = model_definitions

    async def run(self) -> None:
        await self.__initialize_client_on_init()

        self._logger.info("Initialization complete")

    async def destroy(self) -> None:
        if self.__client is not None:
            await self.__client.close()

    @retry(wait=wait_fixed(5))
    async def __initialize_client_on_init(self) -> None:
        try:
            await self.__initialize_client()
        except Exception as error:
            self._logger.error(
                f"Connection error: {str(error)}, retrying in 5 seconds..."
            )
            raise error

    async def __initialize_client(self) -> None:
        self.__client = AsyncMongoClient(self.__url)

        await init_beanie(
            database=self.__client.get_database(self.__name),
            document_models=self.__model_definitions,
        )

    async def reconnect(self, retries: int = 5, delay: float = 2.0) -> None:
        for attempt in range(retries):
            try:
                self._logger.debug(
                    f"An attempt to connect to the document database ({attempt}/{retries})..."
                )

                await self.__initialize_client()

                database = self.__client.get_database(self.__name)
                await database.command("ping")

                self._logger.info(
                    "The connection to the document database has been successfully restored."
                )

            except (ConnectionRefusedError, ServerSelectionTimeoutError) as e:
                self._logger.warning(
                    f"Document database connection error: {e}. Attempt {attempt} from {retries}."
                )

                if attempt < retries:
                    await sleep(delay)
                else:
                    self._logger.error(
                        "The connection to the document database could not be restored."
                    )
                    raise RuntimeError(
                        "The connection to the document database could not be restored."
                    ) from e

    def create_session(self) -> AsyncClientSession:
        """
        Создать экземпляр сессии без контекстного менеджера
        :return:
        """
        return self.__client.start_session()

    # noinspection PyMethodMayBeStatic
    async def close_session(self, session: AsyncClientSession) -> None:
        """
        Закрыть сессию
        :param session:
        :return:
        """
        await session.end_session()
