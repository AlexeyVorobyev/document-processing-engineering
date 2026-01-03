import asyncio
from asyncio import sleep
from dataclasses import dataclass

from qdrant_client import QdrantClient
from tenacity import retry, wait_fixed

from src.common.interfaces.destroyable import IDestroyable
from src.common.interfaces.runnable import IAsyncRunnable
from src.common.logger.logger_mixin import LoggerMixin


@dataclass
class DatabaseConfig:
    address: str
    port: int
    secured: bool
    password: str


class QdrantDatabase(LoggerMixin, IAsyncRunnable, IDestroyable):
    __db_config: DatabaseConfig
    # later move to AsyncQdrantClient, when Async store is available or implement it myself https://github.com/langchain-ai/langchain/issues/32195
    __client: QdrantClient | None

    def __init__(self, db_config: DatabaseConfig) -> None:
        self.__db_config = db_config
        self.__client = None

    async def run(self) -> None:
        await self.__initialize_client_on_init()

        self._logger.info("Initialization complete")

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
        self.__client = QdrantClient(
            host=self.__db_config.address,
            port=self.__db_config.port,
            https=self.__db_config.secured,
            api_key=self.__db_config.password,
        )

    def get_client(self) -> QdrantClient:
        if self.__client is None:
            raise RuntimeError("Connection not initialized")

        return self.__client

    async def destroy(self) -> None:
        if self.__client is None:
            return

        await asyncio.to_thread(self.__client.close)
        self.__client = None
        self._logger.info("Qdrant client connection closed")

    async def reconnect(self, retries: int = 5, delay: float = 2.0) -> None:
        for attempt in range(retries):
            try:
                self._logger.debug(
                    f"An attempt to connect to the qdrant database ({attempt}/{retries})..."
                )

                await self.__initialize_client()

                assert self.__client is not None
                await asyncio.to_thread(self.__client.get_collections)

                self._logger.info(
                    "The connection to the qdrant database has been successfully restored."
                )

            except ConnectionRefusedError as e:
                self._logger.warning(
                    f"Qdrant database connection error: {e}. Attempt {attempt} from {retries}."
                )

                if attempt < retries:
                    await sleep(delay)
                else:
                    self._logger.error(
                        "The connection to the qdrant database could not be restored."
                    )
                    raise RuntimeError(
                        "The connection to the qdrant database could not be restored."
                    ) from e
