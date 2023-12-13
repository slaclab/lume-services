from dependency_injector import containers, providers
from pydantic import ValidationError
from pydantic_settings import BaseSettings
from typing import Optional

from lume_services.services.models.db import ModelDB, ModelDBConfig
from lume_services.services.models import ModelDBService
from lume_services.services.results import (
    ResultsDBService,
    ResultsDB,
)
from lume_services.services.results.mongodb import (
    MongodbResultsDBConfig,
    MongodbResultsDB,
)
from lume_services.services.files import FileService
from lume_services.services.files.filesystems import (
    LocalFilesystem,
    MountedFilesystem,
)
from lume_services.services.scheduling import SchedulingService

from lume_services.errors import EnvironmentNotConfiguredError

import logging


logger = logging.getLogger(__name__)


context: containers.DeclarativeContainer = None
_settings: BaseSettings = None


class Context(containers.DeclarativeContainer):
    config = providers.Configuration()

    filesystems = providers.Dependency(instance_of=list)

    model_db = providers.Dependency(
        ModelDB,
    )

    results_db = providers.Dependency(instance_of=ResultsDB)

    # filter on the case that a filesystem is undefined
    file_service = providers.Singleton(FileService, filesystems=filesystems)

    model_db_service = providers.Singleton(
        ModelDBService,
        model_db=model_db,
    )
    results_db_service = providers.Singleton(
        ResultsDBService,
        results_db=results_db,
    )

    wiring_config = containers.WiringConfiguration(
        packages=[
            "lume_services.files",
            "lume_services.results",
            "lume_services.flows",
            "lume_services.models",
        ],
    )


class LUMEServicesSettings(BaseSettings):
    """Settings describing configuration for default LUME-services provider objects."""

    model_db: Optional[ModelDBConfig]
    results_db: Optional[MongodbResultsDBConfig]
    mounted_filesystem: Optional[MountedFilesystem]
    backend: str = "local"
    # something wrong with pydantic literal parsing?
    # Literal["kubernetes", "local", "docker"] = "local"

    class Config:
        # env_file = '.env'
        # env_file_encoding = 'utf-8'
        validate_assignment = True
        env_prefix = "LUME_"
        env_nested_delimiter = "__"


def configure(settings: Optional[LUMEServicesSettings] = None):
    """Configure method with default methods for lume-services using ModelDB
    and MongodbResultsDB. Populates the global _settings object.

    Args:
        settings (Optional[LUMEServicesSettings]): LUMEServicesSettings object holding
            the runtime configuration for services used by LUME-services.

    """
    logger.info("Configuring LUME-services environment...")
    if settings is None:
        try:
            settings = LUMEServicesSettings()

        except ValidationError as e:
            raise EnvironmentNotConfiguredError(
                get_env_vars(LUMEServicesSettings), validation_error=e
            )

    # apply prefect config
    if settings.prefect is not None:
        settings.prefect.apply()

    global context, _settings
    model_db = None
    if settings.model_db is not None:
        model_db = ModelDB(settings.model_db)

    results_db = None
    if settings.results_db is not None:
        results_db = MongodbResultsDB(settings.results_db)

    filesystems = [
        LocalFilesystem(),
    ]

    if settings.mounted_filesystem is not None:
        filesystems.append(settings.mounted_filesystem)

    context = Context(
        model_db=model_db,
        results_db=results_db,
        filesystems=filesystems,
    )
    _settings = settings
    logger.info("Environment configured.")
    logger.debug("Environment configured using %s", settings.dict())


def get_env_vars(
    settings: type = LUMEServicesSettings,
) -> dict:
    env_vars = {"base": []}

    schema = settings.schema()
    prefix = settings.Config.env_prefix
    delimiter = settings.Config.env_nested_delimiter

    def unpack_props(
        props,
        parent,
        env_vars=env_vars,
        prefix=prefix,
        delimiter=delimiter,
        schema=schema,
    ):

        for prop_name, prop in props.items():
            if "properties" in prop:
                unpack_props(
                    prop["properties"], prefix=f"{prefix}{delimiter}{prop_name}"
                )

            elif "allOf" in prop:

                sub_prop_reference = prop["allOf"][0]["$ref"]
                # prepare from format #/
                sub_prop_reference = sub_prop_reference.replace("#/", "")
                sub_prop_reference = sub_prop_reference.split("/")
                reference_locale = schema
                for reference in sub_prop_reference:
                    reference_locale = reference_locale[reference]

                unpack_props(
                    reference_locale["properties"],
                    parent=parent,
                    prefix=f"{prefix}{delimiter}{prop_name}",
                )

            else:
                if "env_names" in prop:
                    prop_names = list(prop["env_names"])
                    env_vars[parent] += [
                        f"{prefix}{delimiter}{name}".upper() for name in prop_names
                    ]
                else:
                    env_vars[parent].append(f"{prefix}{delimiter}{prop_name}".upper())

    # iterate over top level definitions
    for item_name, item in schema["properties"].items():

        env_name = list(item["env_names"])[0]

        if "allOf" in item:

            sub_prop_reference = item["allOf"][0]["$ref"]
            # prepare from format #/
            sub_prop_reference = sub_prop_reference.replace("#/", "")
            sub_prop_reference = sub_prop_reference.split("/")
            reference_locale = schema
            for reference in sub_prop_reference:
                reference_locale = reference_locale[reference]

            env_vars[item_name] = []
            unpack_props(
                reference_locale["properties"], prefix=env_name, parent=item_name
            )

        else:
            env_vars["base"].append(env_name.upper())

    return env_vars
