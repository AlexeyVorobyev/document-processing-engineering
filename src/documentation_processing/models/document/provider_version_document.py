from datetime import datetime

from beanie import Document
from pydantic import Field

from src.common.dependency_injection.injectable import injectable
from src.documentation_processing.di_tag import DI_TAG


@injectable(container_tags=[DI_TAG])
class ProviderVersionDocument(Document):
    namespace: str = Field(..., description="Terraform provider namespace")
    name: str = Field(..., description="Terraform provider name")
    version: str = Field(..., description="Provider version tag")
    provider_version_id: str = Field(..., description="Provider version identifier from registry")
    pipeline_run_id: str = Field(..., description="Identifier of the pipeline run")
    documents: list[str] = Field(default_factory=list, description="Downloaded document identifiers")
    processed_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "provider_versions"
