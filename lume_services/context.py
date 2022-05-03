from dependency_injector import containers, providers
from lume_services.data.model.model_service import ModelService
from lume_services.data.model.db.db_service import DBService as ModelDBService
from lume_services.data.model.db.db_service import DBServiceConfig as ModelDBServiceConfig
from lume_services.data.results.results_service import ResultsService, ResultsServiceConfig
from lume_services.data.results.db.db_service import DBService as ResultsDBService
from lume_services.data.results.db.db_service import DBServiceConfig as ResultsDBServiceConfig
from lume_services.data.file.service import FileService
from pydantic import BaseSettings, validator
from typing import Any

class Context(containers.DeclarativeContainer):

    config = providers.Configuration()

    results_db_service = providers.Dependency(instance_of=ResultsDBService)
    model_db_service = providers.Dependency(instance_of=ModelDBService)
    file_service = providers.Dependency(instance_of=FileService)

    model_service = providers.Singleton(
        ModelService,
        db_service=model_db_service,
    )

    results_service = providers.Singleton(
        ResultsService,
        db_service=results_db_service,
        model_docs=config.results_service_config.model_docs
    )
    
    wiring_config = containers.WiringConfiguration(
        packages=[
            "lume_services.scheduling",
        ],
    )


class LumeServicesConfig(BaseSettings):
    results_service_config: Any
    model_db_service_config: Any
    results_db_service_config: Any


    @validator("results_service_config")
    def validate_results_service_config(cls, val):
        if issubclass(type(val), ResultsServiceConfig):
            return val

        raise TypeError("results_service_config must be a sublass of ResultsServiceConfig")

    @validator("model_db_service_config")
    def validate_model_db_service_config(cls, val):
        if issubclass(type(val), ModelDBServiceConfig):
            return val

        raise TypeError("model_db_service_config must be a sublass of ModelDBServiceConfig")

    @validator("results_db_service_config")
    def validate_results_db_service_config(cls, val):
        if issubclass(type(val), ResultsDBServiceConfig):
            return val

        raise TypeError("results_db_service_config must be a sublass of ResultsDBServiceConfig")
