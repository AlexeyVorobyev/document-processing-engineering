from beanie import Document
from pydantic import Field

from src.common.dependency_injection.injectable import injectable
from src.documentation_processing.di_tag import DI_TAG


@injectable(container_tags=[DI_TAG])
class ProviderSettings(Document):
    namespace: str = Field(..., description="Terraform provider namespace")
    name: str = Field(..., description="Terraform provider name")
    enabled: bool = Field(default=True, description="Whether provider should be processed")

    class Settings:
        name = "provider_settings"
