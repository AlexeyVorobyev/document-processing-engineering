from enum import StrEnum
from typing import Callable

from dependency_injector.wiring import Provide, inject

from src.common.dependency_injection.injectable import (
    injectable,
)
from src.kdctl.commands.impl.documents_download_command import (
    DocumentsDownloadCommand,
)
from src.kdctl.commands.impl.documents_prepare_command import DocumentsPrepareCommand
from src.kdctl.commands.impl.documents_upload_command import (
    DocumentsUploadCommand,
)
from src.kdctl.commands.impl.documents_vectorize_command import (
    DocumentsVectorizeCommand,
)
from src.kdctl.commands.interface.command import ICommand


class CommandName(StrEnum):
    DOCUMENTS_UPLOAD = "documents-upload"
    DOCUMENTS_DOWNLOAD = "documents-download"
    DOCUMENTS_PREPARE = "documents-prepare"
    DOCUMENTS_VECTORIZE = "documents-vectorize"


type _CommandFactory = Callable[..., ICommand]


@injectable(container_tags=["KDCTL"])
class CommandsFactoryMapping(dict[CommandName, _CommandFactory]):
    def __init__(self) -> None:
        super().__init__(
            {
                CommandName.DOCUMENTS_UPLOAD: self.__documents_upload_command_factory,
                CommandName.DOCUMENTS_DOWNLOAD: self.__documents_download_command_factory,
                CommandName.DOCUMENTS_PREPARE: self.__documents_prepare_command_factory,
                CommandName.DOCUMENTS_VECTORIZE: self.__documents_vectorize_command_factory,
            },
        )

    @inject
    def __documents_upload_command_factory(
        self,
        documents_upload_command: DocumentsUploadCommand = Provide[
            "documents_upload_command"
        ],
    ) -> DocumentsUploadCommand:
        return documents_upload_command

    @inject
    def __documents_download_command_factory(
        self,
        documents_download_command: DocumentsDownloadCommand = Provide[
            "documents_download_command"
        ],
    ) -> DocumentsDownloadCommand:
        return documents_download_command

    @inject
    def __documents_prepare_command_factory(
        self,
        documents_prepare_command: DocumentsPrepareCommand = Provide[
            "documents_prepare_command"
        ],
    ) -> DocumentsPrepareCommand:
        return documents_prepare_command

    @inject
    def __documents_vectorize_command_factory(
        self,
        documents_vectorize_command: DocumentsVectorizeCommand = Provide[
            "documents_vectorize_command"
        ],
    ) -> DocumentsVectorizeCommand:
        return documents_vectorize_command
