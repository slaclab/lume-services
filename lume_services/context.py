from dependency_injector import containers, providers
from lume_services.services.data.models.model_service import ModelService
from lume_services.services.data.models.db.db_service import DBService as ModelDBService
from lume_services.services.data.models.db.db_service import (
    DBServiceConfig as ModelDBServiceConfig,
)
from lume_services.services.data.results import (
    ResultsDBConfig,
    ResultsDBService,
    ResultsDB,
)
from lume_services.services.data.files.service import FileService


from pydantic import BaseSettings, validator
from typing import Any


class Context(containers.DeclarativeContainer):

    config = providers.Configuration()

    results_db = providers.Dependency(instance_of=ResultsDB)
    model_db_service = providers.Dependency(instance_of=ModelDBService)
    file_service = providers.Dependency(instance_of=FileService)

    # scheduling_service = providers.Singleton(
    #    SchedulingService,
    #    ...
    #    file_service = file_service
    # )

    model_service = providers.Singleton(
        ModelService,
        db_service=model_db_service,
    )
    results_db_service = providers.Singleton(
        ResultsDBService,
        results_db=results_db,
    )

    wiring_config = containers.WiringConfiguration(
        packages=[
            "lume_services.services.scheduling",
            "lume_services.services.data.files",
        ],
    )


class LUMEServicesConfig(BaseSettings):
    results_db_service_config: Any
    model_db_service_config: Any

    @validator("model_db_service_config")
    def validate_model_db_service_config(cls, v):
        if issubclass(type(v), ModelDBServiceConfig):
            return v

        raise TypeError(
            "model_db_service_config must be a sublass of ModelDBServiceConfig"
        )

    @validator("results_db_service_config")
    def validate_results_db_service_config(cls, v):
        if issubclass(type(v), ResultsDBConfig):
            return v

        raise TypeError(
            "results_db_service_config must be a sublass of ResultsDBConfig"
        )
