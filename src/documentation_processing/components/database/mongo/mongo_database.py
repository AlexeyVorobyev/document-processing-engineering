from dependency_injector.wiring import Provide

from src.common.database.mongo_database import MongoDatabase as BaseMongoDatabase
from src.common.dependency_injection.injectable import injectable
from src.documentation_processing.di_tag import DI_TAG
from src.documentation_processing.models.model_definitions import ModelDefinitions
from src.documentation_processing.settings import MongoDatabaseSettings


@injectable(container_tags=[DI_TAG])
class MongoDatabase(BaseMongoDatabase):
    def __init__(
        self,
        model_definitions: ModelDefinitions,
        db_config: MongoDatabaseSettings = Provide["settings.provided.db_mongo"],
    ) -> None:
        assert db_config.connection_url is not None
        super().__init__(
            model_definitions=model_definitions,
            url=db_config.connection_url,
            name=db_config.name,
        )
