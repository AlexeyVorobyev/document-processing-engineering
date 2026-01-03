from datetime import datetime

import aiohttp

from src.common.dependency_injection.injectable import injectable
from src.common.logger.logger_mixin import LoggerMixin
from src.documentation_processing.di_tag import DI_TAG
from src.documentation_processing.models.document import ProviderVersionDocument
from src.documentation_processing.models.internal import PipelineState, ProviderVersion
from src.documentation_processing.nodes.interface.node import INode

_PROVIDER_VERSIONS_INCLUDE = "provider-versions"


@injectable(container_tags=[DI_TAG])
class ProviderVersionSelectionNode(LoggerMixin, INode[PipelineState]):
    async def execute(self, state: PipelineState) -> PipelineState:
        self._logger.info("Selecting provider versions...")
        return await self.__execute(state)

    async def __execute(self, state: PipelineState) -> PipelineState:
        selected_versions: list[ProviderVersion] = []

        async with aiohttp.ClientSession() as session:
            for provider in state.providers:
                url = (
                    "https://registry.terraform.io/v2/providers/"
                    f"{provider.namespace}/{provider.name}?include={_PROVIDER_VERSIONS_INCLUDE}"
                )

                async with session.get(url) as response:
                    response.raise_for_status()
                    payload = await response.json()

                versions_raw = [
                    item
                    for item in payload.get("included", [])
                    if item.get("type") == _PROVIDER_VERSIONS_INCLUDE
                ]

                if not versions_raw:
                    self._logger.warning(
                        "No versions found for provider %s", provider.slug
                    )
                    continue

                latest_version = max(
                    versions_raw,
                    key=lambda item: item.get("attributes", {}).get(
                        "published-at", datetime.min.isoformat()
                    ),
                )

                version_value = latest_version.get("attributes", {}).get("version")
                version_id = latest_version.get("id")

                if version_value is None or version_id is None:
                    self._logger.warning(
                        "Skip provider %s due to missing version metadata",
                        provider.slug,
                    )
                    continue

                already_processed = await ProviderVersionDocument.find_one(
                    ProviderVersionDocument.namespace == provider.namespace,
                    ProviderVersionDocument.name == provider.name,
                    ProviderVersionDocument.version == version_value,
                )

                if already_processed is not None:
                    self._logger.info(
                        "Provider %s already processed for version %s",
                        provider.slug,
                        version_value,
                    )
                    continue

                selected_versions.append(
                    ProviderVersion(
                        provider=provider,
                        version=version_value,
                        provider_version_id=str(version_id),
                    )
                )

        state.versions_to_process = selected_versions
        return state
