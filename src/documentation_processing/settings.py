from typing import Any

from pydantic import (
    BaseModel,
    MongoDsn,
    field_validator,
)
from pydantic_core.core_schema import ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.common.dependency_injection.injectable import injectable
from src.common.logger.logger import Level
from src.documentation_processing.di_tag import DI_TAG


class AppSettings(BaseModel):
    app_name: str = "DOCUMENTATION-PROCESSING-BACKEND"
    vector_database_collection: str = "knowledge_collection_2"
    log_level: Level = "DEBUG"
    dev_mode: bool = False
    openai_api_key: str = "<NOT_SPECIFIED>"
    model_name: str = "text-embedding-3-large"
    llm_base_url: str | None = None


class MongoDatabaseSettings(BaseSettings):
    user: str = "dpb_app"
    name: str = "dpb_app"
    password: str = "dpb_app_password"
    port: int = 27017
    address: str = "127.0.0.1"
    max_overflow: int = 50
    reconnect_max_retries: int = 2
    reconnect_retry_delay: float = 2.0

    connection_url: str | None = None

    @field_validator("connection_url", mode="before")
    @classmethod
    def assemble_connection_url(cls, v: str | None, values: ValidationInfo) -> Any:
        if isinstance(v, str):
            return v

        return MongoDsn.build(
            scheme="mongodb",
            username=values.data.get("user"),
            password=values.data.get("password"),
            host=values.data.get("address"),
            port=values.data.get("port"),
            path="?connectTimeoutMS=2000&serverSelectionTimeoutMS=2000",
        ).unicode_string()


class QdrantDatabaseSettings(BaseSettings):
    port: int = 6333
    address: str = "127.0.0.1"
    secured: bool = False
    password: str = "dpb_app_password"


@injectable(container_tags=[DI_TAG])
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        validate_default=False,
        env_prefix="DPB_",
        env_nested_delimiter="__",
    )

    app: AppSettings = AppSettings()
    db_mongo: MongoDatabaseSettings = MongoDatabaseSettings()
    db_qdrant: QdrantDatabaseSettings = QdrantDatabaseSettings()
