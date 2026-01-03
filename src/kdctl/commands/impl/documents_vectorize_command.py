import asyncio
import traceback
from argparse import Namespace
from pathlib import Path
from typing import cast

from langchain_openai import OpenAIEmbeddings
from pydantic import SecretStr

from src.common.dependency_injection.injectable import injectable
from src.common.logger.logger_mixin import LoggerMixin
from src.common.utils.fs_utils import load_json_from_file, save_json_to_file
from src.kdctl.commands.impl.documents_download_command import dataclass
from src.kdctl.commands.interface.command import ICommand
from src.kdctl.types.document import Document


@dataclass
class _CommandArgs:
    input_folder_path: Path
    output_folder_path: Path
    api_key: SecretStr
    base_url: str | None
    model: str


@injectable(container_tags=["KDCTL"])
class DocumentsVectorizeCommand(LoggerMixin, ICommand):
    async def execute(self, namespace: Namespace) -> None:
        args = self.__extract_args(namespace)
        args.output_folder_path.mkdir(exist_ok=True, parents=True)

        self._logger.info("Vectorizing documents...")

        file_paths = (
            file
            for file in args.input_folder_path.iterdir()
            if file.is_file() and ".json" in str(file)
        )

        llm = self.__get_llm(args)

        await asyncio.gather(
            *(
                self.__vectorize_document(file_path, args.output_folder_path, llm)
                for file_path in file_paths
            )
        )

    async def __vectorize_document(
        self, path: Path, output_folder_path: Path, llm: OpenAIEmbeddings
    ) -> None:
        try:
            data = cast(Document, await load_json_from_file(path))
        except Exception as error:
            self._logger.warning(
                f"Cant read file '{path}', {traceback.format_exception_only(error)}:{error}"
            )
            return

        data["vector"] = await llm.aembed_query(data["payload"]["page_content"])

        try:
            await save_json_to_file(output_folder_path / path.name, data)
        except Exception as error:
            self._logger.warning(
                f"Cant write file '{path}', {traceback.format_exception_only(error)}:{error}"
            )
            return

        self._logger.info(f"Vectorized file '{path}' successfully")

    def __extract_args(self, namespace: Namespace) -> _CommandArgs:
        return _CommandArgs(
            output_folder_path=Path(namespace.output),
            input_folder_path=Path(namespace.input),
            api_key=SecretStr(namespace.api_key),
            base_url=namespace.base_url,
            model=namespace.model,
        )

    def __get_llm(self, args: _CommandArgs) -> OpenAIEmbeddings:
        return OpenAIEmbeddings(
            api_key=args.api_key, base_url=args.base_url, model=args.model
        )
