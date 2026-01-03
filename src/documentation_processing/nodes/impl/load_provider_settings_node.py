from src.common.dependency_injection.injectable import injectable
from src.common.logger.logger_mixin import LoggerMixin
from src.documentation_processing.di_tag import DI_TAG
from src.documentation_processing.models.document import ProviderSettings
from src.documentation_processing.models.internal import PipelineState, ProviderConfig
from src.documentation_processing.nodes.interface.node import INode


@injectable(container_tags=[DI_TAG])
class LoadProviderSettingsNode(LoggerMixin, INode[PipelineState]):
    async def execute(self, state: PipelineState) -> PipelineState:
        self._logger.info("Loading provider settings...")
        return await self.__execute(state)

    async def __execute(self, state: PipelineState) -> PipelineState:
        provider_settings = await ProviderSettings.find(
            ProviderSettings.enabled == True  # noqa: E712
        ).to_list()

        state.providers = [
            ProviderConfig(namespace=provider.namespace, name=provider.name)
            for provider in provider_settings
        ]

        self._logger.debug(f"Settings = {state.providers}")

        return state
