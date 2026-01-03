from beanie import Document

from src.common.dependency_injection.injectable import injectable
from src.documentation_processing.models.document import (
    ProviderSettings,
    ProviderVersionDocument,
)
from src.documentation_processing.di_tag import DI_TAG


@injectable(container_tags=[DI_TAG])
class ModelDefinitions(list[type[Document]]):
    def __init__(self) -> None:
        super().__init__([
            ProviderSettings,
            ProviderVersionDocument,
        ])
