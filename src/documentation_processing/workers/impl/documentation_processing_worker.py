from datetime import timedelta

from src.common.dependency_injection.injectable import injectable
from src.common.workers.base_asyncio_worker import BaseAsyncioWorker
from src.documentation_processing.di_tag import DI_TAG
from src.documentation_processing.pipelines.impl import DocumentationPipeline


@injectable(container_tags=[DI_TAG])
class DocumentationProcessingWorker(BaseAsyncioWorker):
    def __init__(self, pipeline: DocumentationPipeline) -> None:
        super().__init__()
        self.__pipeline = pipeline

    async def _worker(self) -> None:
        self._logger.info("Starting documentation processing pipeline...")
        await self.__pipeline.execute(None)
        self._logger.info("Documentation processing pipeline completed.")

    @property
    def _worker_interval(self) -> int:
        return int(timedelta(days=1).total_seconds())
