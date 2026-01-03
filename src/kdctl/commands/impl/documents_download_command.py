import asyncio
from argparse import Namespace
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from qdrant_client import AsyncQdrantClient

from src.common.dependency_injection.injectable import (
    injectable,
)
from src.common.logger.logger_mixin import LoggerMixin
from src.common.utils.fs_utils import save_json_to_file
from src.kdctl.commands.interface.command import ICommand
from src.kdctl.types.document import Document, DocumentPayload, Vector


@dataclass
class _CommandArgs:
    port: int
    host: str
    password: str
    secured: bool
    collection: str
    output_folder_path: Path


@injectable(container_tags=["KDCTL"])
class DocumentsDownloadCommand(LoggerMixin, ICommand):
    __BATCH_SIZE = 10

    async def execute(self, namespace: Namespace) -> None:
        args = self.__extract_args(namespace)
        args.output_folder_path.mkdir(exist_ok=True, parents=True)
        self._logger.info(f"Downloading documents from '{args.host}'...")

        client = self.__get_client(args)

        self._logger.info(f"Saving documents into {args.output_folder_path}...")

        offset = None

        while True:
            documents, next_offset = await client.scroll(
                collection_name=args.collection,
                limit=self.__BATCH_SIZE,
                offset=offset,
                with_payload=True,
                with_vectors=True,
            )

            await asyncio.gather(
                *(
                    self.__save_document(
                        output_folder_path=args.output_folder_path,
                        document={
                            "id": str(document.id),
                            "payload": cast(DocumentPayload, document.payload),
                            "vector": cast(Vector, document.vector),
                        },
                    )
                    for document in documents
                )
            )

            if next_offset is None:
                break

            offset = next_offset

    async def __save_document(
        self, output_folder_path: Path, document: Document
    ) -> None:
        name = document["payload"]["metadata"]["name"]
        await save_json_to_file(
            file_path=output_folder_path / Path(f"{name}.json"),
            content=document,
        )

        self._logger.info(
            f"Successfully saved document with id='{document['id']}', name='{name}'"
        )

    def __extract_args(self, namespace: Namespace) -> _CommandArgs:
        return _CommandArgs(
            port=namespace.port,
            host=namespace.host,
            password=namespace.password,
            secured=namespace.secured,
            collection=namespace.collection,
            output_folder_path=Path(namespace.output),
        )

    def __get_client(self, args: _CommandArgs) -> AsyncQdrantClient:
        return AsyncQdrantClient(
            port=args.port,
            host=args.host,
            https=args.secured,
            api_key=args.password,
        )
