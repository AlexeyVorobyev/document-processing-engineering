import json
from asyncio import create_subprocess_exec
from asyncio.subprocess import PIPE
from pathlib import Path

import aiohttp

from src.common.dependency_injection.injectable import injectable
from src.common.logger.logger_mixin import LoggerMixin
from src.documentation_processing.di_tag import DI_TAG
from src.documentation_processing.models.document import ProviderVersionDocument
from src.documentation_processing.models.internal import PipelineState, ProviderVersion
from src.documentation_processing.nodes.interface.node import INode
from src.documentation_processing.settings import Settings

_PROVIDER_DOCS_INCLUDE = "provider-docs"


@injectable(container_tags=[DI_TAG])
class ProcessProviderVersionNode(LoggerMixin, INode[PipelineState]):
    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self.__settings = settings

    async def execute(self, state: PipelineState) -> PipelineState:
        self._logger.info("Processing versions...")
        return await self.__execute(state)

    async def __execute(self, state: PipelineState) -> PipelineState:
        if not state.versions_to_process:
            self._logger.info("No provider versions selected for processing")
            return state

        workspace_root = state.workspace_root / str(state.run_id)
        raw_documents_dir = workspace_root / "raw_documents"
        combined_dir = workspace_root / "raw_documents_combined"
        prepared_dir = workspace_root / "prepared"
        vectorized_dir = workspace_root / "vectorized"

        raw_documents_dir.mkdir(parents=True, exist_ok=True)
        combined_dir.mkdir(parents=True, exist_ok=True)
        prepared_dir.mkdir(parents=True, exist_ok=True)
        vectorized_dir.mkdir(parents=True, exist_ok=True)

        async with aiohttp.ClientSession() as session:
            for version in state.versions_to_process:
                await self.__process_version(
                    session=session,
                    version=version,
                    raw_documents_dir=raw_documents_dir,
                    combined_dir=combined_dir,
                    prepared_dir=prepared_dir,
                    vectorized_dir=vectorized_dir,
                    run_id=str(state.run_id),
                )

        return state

    async def __process_version(
        self,
        *,
        session: aiohttp.ClientSession,
        version: ProviderVersion,
        raw_documents_dir: Path,
        combined_dir: Path,
        prepared_dir: Path,
        vectorized_dir: Path,
        run_id: str,
    ) -> None:
        provider_docs = await self.__fetch_provider_docs(session, version)

        if not provider_docs:
            self._logger.warning(
                "No documentation entries for %s %s",
                version.provider.slug,
                version.version,
            )
            return

        downloaded_documents = await self.__download_documents(
            session=session,
            documents=provider_docs,
            destination=raw_documents_dir,
        )

        combined_path = self.__combine_documents(
            provider_version=version,
            document_ids=downloaded_documents,
            source_dir=raw_documents_dir,
            destination_dir=combined_dir,
        )

        prepared_output_dir = prepared_dir / (
            f"{version.provider.namespace}_{version.provider.name}_{version.version}"
        )
        prepared_output_dir.mkdir(parents=True, exist_ok=True)

        metadata = {
            "provider": version.provider.slug,
            "version": version.version,
            "run_id": run_id,
        }

        await self.__run_kdctl_prepare(
            input_path=combined_path,
            output_dir=prepared_output_dir,
            metadata=metadata,
        )

        vectorized_output_dir = vectorized_dir / (
            f"{version.provider.namespace}_{version.provider.name}_{version.version}"
        )
        vectorized_output_dir.mkdir(parents=True, exist_ok=True)

        await self.__run_kdctl_vectorize(
            input_dir=prepared_output_dir,
            output_dir=vectorized_output_dir,
        )

        await self.__run_kdctl_upload(input_dir=vectorized_output_dir)

        await ProviderVersionDocument(
            namespace=version.provider.namespace,
            name=version.provider.name,
            version=version.version,
            provider_version_id=version.provider_version_id,
            pipeline_run_id=run_id,
            documents=downloaded_documents,
        ).insert()

    async def __fetch_provider_docs(
        self, session: aiohttp.ClientSession, version: ProviderVersion
    ) -> list[str]:
        url = (
            "https://registry.terraform.io/v2/provider-versions/"
            f"{version.provider_version_id}?include={_PROVIDER_DOCS_INCLUDE}"
        )

        async with session.get(url) as response:
            response.raise_for_status()
            payload = await response.json()

        return [
            item["id"]
            for item in payload.get("included", [])
            if item.get("type") == _PROVIDER_DOCS_INCLUDE and item.get("id") is not None
        ]

    async def __download_documents(
        self,
        *,
        session: aiohttp.ClientSession,
        documents: list[str],
        destination: Path,
    ) -> list[str]:
        downloaded: list[str] = []

        for document_id in documents:
            url = f"https://registry.terraform.io/v2/provider-docs/{document_id}"

            async with session.get(url) as response:
                response.raise_for_status()
                payload = await response.json()

            content = payload.get("data", {}).get("attributes", {}).get("content", "")

            file_path = destination / f"{document_id}.md"
            file_path.write_text(content)
            downloaded.append(document_id)

        return downloaded

    def __combine_documents(
        self,
        *,
        provider_version: ProviderVersion,
        document_ids: list[str],
        source_dir: Path,
        destination_dir: Path,
    ) -> Path:
        combined_path = destination_dir / (
            f"{provider_version.provider.namespace}_"
            f"{provider_version.provider.name}_{provider_version.version}.md"
        )

        combined_content = []
        for document_id in document_ids:
            document_path = source_dir / f"{document_id}.md"
            if document_path.exists():
                combined_content.append(document_path.read_text())

        combined_path.write_text("\n\n".join(combined_content))
        return combined_path

    async def __run_kdctl_prepare(
        self,
        *,
        input_path: Path,
        output_dir: Path,
        metadata: dict[str, str],
    ) -> None:
        command = [
            "python3.13",
            "-m",
            "src.kdctl.main",
            "documents-prepare",
            "--api-key",
            self.__settings.app.openai_api_key,
            "--input",
            str(input_path),
            "--output",
            str(output_dir),
            "--metadata",
            json.dumps(metadata),
        ]

        if self.__settings.app.llm_base_url:
            command.extend(["--base-url", self.__settings.app.llm_base_url])

        await self.__run_command(command)

    async def __run_kdctl_vectorize(
        self,
        *,
        input_dir: Path,
        output_dir: Path,
    ) -> None:
        command = [
            "python3.13",
            "-m",
            "src.kdctl.main",
            "documents-vectorize",
            "--api-key",
            self.__settings.app.openai_api_key,
            "--model",
            self.__settings.app.model_name,
            "--input",
            str(input_dir),
            "--output",
            str(output_dir),
        ]

        if self.__settings.app.llm_base_url:
            command.extend(["--base-url", self.__settings.app.llm_base_url])

        await self.__run_command(command)

    async def __run_kdctl_upload(self, *, input_dir: Path) -> None:
        command = [
            "python3.13",
            "-m",
            "src.kdctl.main",
            "documents-upload",
            "--host",
            self.__settings.db_qdrant.address,
            "--port",
            str(self.__settings.db_qdrant.port),
            "--password",
            self.__settings.db_qdrant.password,
            "--collection",
            self.__settings.app.vector_database_collection,
            "--input",
            str(input_dir),
        ]

        if self.__settings.db_qdrant.secured:
            command.append("--secured")

        await self.__run_command(command)

    async def __run_command(self, command: list[str]) -> None:
        self._logger.debug(f"Executing: {" ".join(command)}")
        process = await create_subprocess_exec(*command, stdout=PIPE, stderr=PIPE)
        stdout, stderr = await process.communicate()

        if stdout:
            self._logger.debug(stdout.decode())
        if stderr:
            self._logger.error(stderr.decode())

        if process.returncode != 0:
            raise RuntimeError(
                f"Command {' '.join(command)} failed with code {process.returncode}"
            )
