from dataclasses import dataclass, field
from pathlib import Path
from uuid import UUID


@dataclass
class ProviderConfig:
    namespace: str
    name: str

    @property
    def slug(self) -> str:
        return f"{self.namespace}/{self.name}"


@dataclass
class ProviderVersion:
    provider: ProviderConfig
    version: str
    provider_version_id: str
    documents: list[str] = field(default_factory=list)


@dataclass
class PipelineState:
    run_id: UUID
    providers: list[ProviderConfig] = field(default_factory=list)
    versions_to_process: list[ProviderVersion] = field(default_factory=list)
    workspace_root: Path = field(
        default_factory=lambda: Path("src/workspace/documentation_processing")
    )
