import os
from dependency_injector import containers, providers
from pydantic import BaseSettings, ValidationError
from typing import Optional

from lume_services.services.models.db import ModelDB
from lume_services.services.models import ModelDBService
from lume_services.services.models.db.mysql import MySQLModelDBConfig, MySQLModelDB
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
from lume_services.services.scheduling import PrefectConfig


import logging


logger = logging.getLogger(__name__)


context: containers.DeclarativeContainer = None
_settings: BaseSettings = None


class Context(containers.DeclarativeContainer):
    config = providers.Configuration()

    mounted_filesystem = providers.Dependency(
        instance_of=MountedFilesystem, default=None
    )
    local_filesystem = providers.Singleton(
        LocalFilesystem,
    )

    model_db = providers.Dependency(
        ModelDB,
    )

    results_db = providers.Dependency(instance_of=ResultsDB)

    # filter on the case that a filesystem is undefiled
    file_service = providers.Singleton(
        FileService, filesystems=providers.List(local_filesystem, mounted_filesystem)
    )

    model_db_service = providers.Singleton(
        ModelDBService,
        model_db=model_db,
    )
    results_db_service = providers.Singleton(
        ResultsDBService,
        results_db=results_db,
    )

    # scheduling_service = providers.Singleton(
    #    SchedulingService,
    #    config=config.scheduling
    # )

    wiring_config = containers.WiringConfiguration(
        packages=[
            "lume_services.files",
            "lume_services.results",
        ],
    )


class LUMEServicesSettings(BaseSettings):
    """Settings describing configuration for default LUME-services provider objects."""

    model_db: MySQLModelDBConfig
    results_db: MongodbResultsDBConfig
    prefect: Optional[PrefectConfig]
    mounted_filesystem: Optional[MountedFilesystem]

    class Config:
        # env_file = '.env'
        # env_file_encoding = 'utf-8'
        validate_assignment = True
        env_prefix = "LUME_"
        env_nested_delimiter = "__"


class EnvironmentNotConfiguredError(Exception):
    def __init__(self, env_vars, validation_error: ValidationError):
        self.env = os.environ
        self.env_vars = []

        for service in env_vars:
            self.env_vars += env_vars[service]

        self.missing_vars = [var for var in self.env_vars if var not in self.env]

        self.message = """%s. Evironment variables not defined: %s"
        """

        super().__init__(
            self.message, str(validation_error), ", ".join(self.missing_vars)
        )


def configure(settings: LUMEServicesSettings = None):
    """Configure method with default methods for lume-services using MySQLModelDB
    and MongodbResultsDB.

    """
    if not settings:
        try:
            settings = LUMEServicesSettings()

        except ValidationError as e:
            raise EnvironmentNotConfiguredError(
                list_env_vars(LUMEServicesSettings.schema()), validation_error=e
            )

    global context, _settings
    model_db = MySQLModelDB(settings.model_db)
    results_db = MongodbResultsDB(settings.results_db)

    context = Context(
        model_db=model_db,
        results_db=results_db,
        mounted_filesystem=settings.mounted_filesystem,
    )
    _settings = settings


def list_env_vars(
    schema: dict = LUMEServicesSettings.schema(),
    prefix: str = LUMEServicesSettings.Config.env_prefix,
    delimiter: str = LUMEServicesSettings.Config.env_nested_delimiter,
) -> list:
    env_vars = {"base": []}

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

    # capitalize

    return env_vars
