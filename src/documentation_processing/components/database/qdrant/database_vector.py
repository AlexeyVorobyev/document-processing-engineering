from dependency_injector.wiring import Provide

from src.ai_agent_infrastructure.settings import DatabaseVectorSettings
from src.common.database.qdrant_database import DatabaseConfig, QdrantDatabase
from src.common.dependency_injection.injectable import (
    injectable,
)


@injectable()
class DatabaseVector(QdrantDatabase):
    def __init__(
        self,
        db_config: DatabaseVectorSettings = Provide["settings.provided.db_vector"],
    ) -> None:
        super().__init__(
            DatabaseConfig(
                address=db_config.address,
                port=db_config.port,
                secured=db_config.secured,
                password=db_config.password,
            )
        )
