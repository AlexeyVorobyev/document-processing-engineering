from uuid import uuid4

from src.common.dependency_injection.injectable import injectable
from src.common.logger.logger_mixin import LoggerMixin
from src.documentation_processing.models.internal import PipelineState
from src.documentation_processing.di_tag import DI_TAG
from src.documentation_processing.nodes.impl.load_provider_settings_node import (
    LoadProviderSettingsNode,
)
from src.documentation_processing.nodes.impl.process_provider_version_node import (
    ProcessProviderVersionNode,
)
from src.documentation_processing.nodes.impl.provider_version_selection_node import (
    ProviderVersionSelectionNode,
)
from src.documentation_processing.pipelines.interface.pipeline import IPipeline


@injectable(container_tags=[DI_TAG])
class DocumentationPipeline(LoggerMixin, IPipeline[None, PipelineState, None]):
    def __init__(
        self,
        load_provider_settings_node: LoadProviderSettingsNode,
        provider_version_selection_node: ProviderVersionSelectionNode,
        process_provider_version_node: ProcessProviderVersionNode,
    ) -> None:
        super().__init__()
        self.__load_provider_settings_node = load_provider_settings_node
        self.__provider_version_selection_node = provider_version_selection_node
        self.__process_provider_version_node = process_provider_version_node

    def _convert_input_to_state(self, input: None) -> PipelineState:  # noqa: A002
        return PipelineState(run_id=uuid4())

    def _convert_state_to_output(self, state: PipelineState) -> None:  # type: ignore[override]
        return None

    async def execute(self, input: None) -> None:  # noqa: A002
        return await self.__execute(input)

    async def __execute(self, input: None) -> None:  # noqa: A002
        state = self._convert_input_to_state(input)

        state = await self.__load_provider_settings_node.execute(state)
        state = await self.__provider_version_selection_node.execute(state)
        await self.__process_provider_version_node.execute(state)

        self._logger.info(
            "Documentation pipeline finished for run %s", state.run_id
        )
