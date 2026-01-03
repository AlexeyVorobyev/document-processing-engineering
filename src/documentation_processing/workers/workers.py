from src.common.dependency_injection.injectable import injectable
from src.common.interfaces.runnable import ISyncRunnable
from src.common.workers.base_asyncio_worker import BaseAsyncioWorker
from src.documentation_processing.workers.impl.documentation_processing_worker import (
    DocumentationProcessingWorker,
)
from src.documentation_processing.di_tag import DI_TAG


@injectable(container_tags=[DI_TAG])
class Workers(list[BaseAsyncioWorker], ISyncRunnable):
    def __init__(self, documentation_processing_worker: DocumentationProcessingWorker) -> None:
        super().__init__([documentation_processing_worker])

    def run(self) -> None:
        for worker in self:
            worker.run()

    def stop(self) -> None:
        for worker in self:
            if worker.is_running:
                worker.stop()
