import asyncio
import traceback
from argparse import Namespace
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import PointStruct
from qdrant_client.models import Distance, VectorParams

from src.common.dependency_injection.injectable import (
    injectable,
)
from src.common.logger.logger_mixin import LoggerMixin
from src.common.utils.fs_utils import load_json_from_file
from src.kdctl.commands.interface.command import ICommand
from src.kdctl.types.document import Document


@dataclass
class _CommandArgs:
    port: int
    host: str
    password: str
    secured: bool
    collection: str
    input_folder_path: Path


@injectable(container_tags=["KDCTL"])
class DocumentsUploadCommand(LoggerMixin, ICommand):
    async def execute(self, namespace: Namespace) -> None:
        args = self.__extract_args(namespace)
        client = self.__get_client(args)

        if not await client.collection_exists(args.collection):
            await client.create_collection(
                collection_name=args.collection,
                vectors_config={"": VectorParams(size=3072, distance=Distance.COSINE)},
            )
            self._logger.info(f"Created collection '{args.collection}'")

        self._logger.info(f"Uploading documents to '{args.host}'")

        file_paths = [
            file
            for file in args.input_folder_path.iterdir()
            if file.is_file() and ".json" in str(file)
        ]

        if not file_paths:
            self._logger.warning("Directory is empty")

        await asyncio.gather(
            *(
                self.__upload_document(file_path, client, args.collection)
                for file_path in file_paths
            )
        )

    async def __upload_document(
        self, path: Path, client: AsyncQdrantClient, collection: str
    ) -> None:
        self._logger.info(f"Uploading file '{path}'...")

        try:
            data = cast(Document, await load_json_from_file(path))
        except Exception as error:
            self._logger.warning(
                f"Cant read file '{path}', {traceback.format_exception_only(error)}:{error}"
            )
            return

        if data["vector"] is not None:
            vector = data["vector"]
        else:
            self._logger.warning(f"File '{path}', not vectorized.")
            return

        try:
            await client.upsert(
                collection_name=collection,
                points=[
                    PointStruct(
                        id=data["id"],
                        payload=cast(dict[str, Any], data["payload"]),
                        vector=vector,
                    )
                ],
            )
        except Exception as error:
            self._logger.warning(
                f"Cant load file '{path}', {traceback.format_exception_only(error)}:{error}"
            )
            return

        self._logger.info(f"Uploaded file '{path}' successfully")

    def __extract_args(self, namespace: Namespace) -> _CommandArgs:
        return _CommandArgs(
            port=namespace.port,
            host=namespace.host,
            password=namespace.password,
            secured=namespace.secured,
            collection=namespace.collection,
            input_folder_path=Path(namespace.input),
        )

    def __get_client(self, args: _CommandArgs) -> AsyncQdrantClient:
        return AsyncQdrantClient(
            port=args.port,
            host=args.host,
            https=args.secured,
            api_key=args.password,
        )
