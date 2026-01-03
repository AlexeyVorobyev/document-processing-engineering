import asyncio
import json
import math
import re
from argparse import Namespace
from pathlib import Path
from typing import Any
from uuid import uuid4

from langchain.chat_models import BaseChatModel
from langchain.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, SecretStr

from src.common.dependency_injection.injectable import injectable
from src.common.logger.logger_mixin import LoggerMixin
from src.common.utils.fs_utils import load_data_from_file, save_json_to_file
from src.kdctl.commands.impl.documents_download_command import dataclass
from src.kdctl.commands.interface.command import ICommand
from src.kdctl.types.document import Document


@dataclass
class _CommandArgs:
    input_file_path: Path
    output_folder_path: Path
    api_key: SecretStr
    base_url: str | None
    model: str
    metadata: dict[str, Any]


class _Chunk(BaseModel):
    title: str = Field(description="Short, descriptive title of the section")
    content: str = Field(description="Full original text of the section")


class _SegmentationOutput(BaseModel):
    documents: list[_Chunk] = Field(
        description="List of logically separated documentation sections"
    )


@injectable(container_tags=["KDCTL"])
class DocumentsPrepareCommand(LoggerMixin, ICommand):
    async def execute(self, namespace: Namespace) -> None:
        args = self.__extract_args(namespace)
        args.output_folder_path.mkdir(exist_ok=True, parents=True)

        llm = self.__get_llm(args)
        raw_data = await load_data_from_file(args.input_file_path)

        chunks = await self.__split_document(text=raw_data, llm=llm)

        created_documents_names = set[str]()

        await asyncio.gather(
            *(
                self.__save_document(
                    output_folder_path=args.output_folder_path,
                    document={
                        "id": str(uuid4()),
                        "payload": {
                            "page_content": chunk.content.strip(),
                            "metadata": {
                                "name": self.__normalize_name(chunk.title.strip()),
                                **args.metadata,
                            },
                        },
                        "vector": None,
                    },
                    created_documents_names=created_documents_names,
                )
                for chunk in chunks
            )
        )

    def __normalize_name(self, name: str) -> str:
        name = re.sub(r"\.[a-zA-Z0-9]+$", "", name)

        return (
            name.replace(" ", "_")
            .replace("/", "_")
            .replace("(", "")
            .replace(")", "")
            .replace(":", "")
            .lower()
        )

    async def __save_document(
        self,
        output_folder_path: Path,
        document: Document,
        created_documents_names: set[str],
    ) -> None:
        name = document["payload"]["metadata"]["name"]

        if name in created_documents_names:
            self._logger.warning(
                f"Document with name='{name}' already created. Possible cause - llm created documents with same name"
            )
            return
        else:
            created_documents_names.add(name)

        await save_json_to_file(
            file_path=output_folder_path / Path(f"{name}.json"),
            content=document,
        )

        self._logger.info(
            f"Successfully saved document with id='{document['id']}', name='{name}'"
        )

    def __extract_args(self, namespace: Namespace) -> _CommandArgs:
        return _CommandArgs(
            output_folder_path=Path(namespace.output),
            input_file_path=Path(namespace.input),
            api_key=SecretStr(namespace.api_key),
            base_url=namespace.base_url,
            model=namespace.model,
            metadata=json.loads(namespace.metadata),
        )

    def __get_llm(self, args: _CommandArgs) -> ChatOpenAI:
        return ChatOpenAI(
            api_key=args.api_key, base_url=args.base_url, model=args.model
        )

    async def __split_document(self, text: str, llm: BaseChatModel) -> list[_Chunk]:
        """
        Splits large documentation into several large chunks and sends them
        in parallel to LLM with structured output to produce semantically
        segmented subdocuments. No summarization or simplification allowed.
        """

        system_prompt = (
            "You are an expert technical editor specializing in Terraform and cloud infrastructure documentation. "
            "Your task is to split the following text into logically distinct subdocuments. "
            "Each subdocument should correspond to a meaningful section that can be read independently. "
            "Do NOT summarize, simplify, or rephrase. "
            "Preserve every technical detail, example, and configuration line exactly as in the original. "
            "Your output must preserve meaning and internal structure while only splitting into sections."
        )

        text_len = len(text)
        num_parts = max(2, min(6, math.ceil(text_len / 50000)))
        chunk_size = math.ceil(text_len / num_parts)

        chunks = [text[i : i + chunk_size] for i in range(0, text_len, chunk_size)]
        self._logger.info(
            f"📚 Splitting document into {len(chunks)} parts for parallel LLM segmentation..."
        )

        structured_llm = llm.with_structured_output(_SegmentationOutput)

        async def process_chunk(chunk: str, idx: int) -> list[_Chunk]:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=chunk),
            ]

            self._logger.info(f"Sending chunk {idx + 1}/{len(chunks)} to LLM...")
            try:
                response = await structured_llm.ainvoke(messages)
                model = _SegmentationOutput.model_validate(response)
                self._logger.info(
                    f"Chunk {idx + 1} processed: {len(model.documents)} sections."
                )
                return model.documents
            except Exception as e:
                self._logger.warning(f"LLM failed on chunk {idx + 1}: {e}")
                return []

        results = await asyncio.gather(
            *(process_chunk(chunk, i) for i, chunk in enumerate(chunks))
        )

        all_docs: list[_Chunk] = [doc for part in results for doc in part]

        self._logger.info(
            f"Successfully segmented total {len(all_docs)} logical subdocuments."
        )

        return all_docs
