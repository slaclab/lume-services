import logging
from dependency_injector.wiring import Provide, inject
from prefect import task
from typing import Any

from lume_services.config import Context
from lume_services.services.data.files import FileService
from prefect.engine.results import PrefectResult

from lume_services.data.files import get_file_from_serializer_string
from lume_services.utils import fingerprint_dict

logger = logging.getLogger(__name__)


def unique_file_location(flow_id, parameters):
    parameters["flow_id"] = flow_id
    hash = fingerprint_dict(parameters)
    return f"{hash}.prefect"


@inject
@task(log_stdout=True, result=PrefectResult(location=unique_file_location))
def save_file(
    obj: Any,
    filename: str,
    filesystem_identifier: str,
    file_type: type,
    file_service: FileService = Provide[Context.file_service],
):
    """Save a file

    Args:
        obj (Any): Object to be saved
        filename (str): File path to save
        filesystem_identifier (str): String identifier for filesystem configured with
            File Service
        file_type (type): Type of file to save as
        file_service (FileService): File service for interacting w/ filesystems

    Returns:
        dict: Loaded file type

    """
    file = file_type(
        obj=obj, filesystem_identifier=filesystem_identifier, filename=filename
    )
    file.write(file_service=file_service)
    return file.jsonable_dict()


@inject
@task()
def load_file(
    file_rep: dict, file_service: FileService = Provide[Context.file_service]
) -> Any:
    """Load a file

    Args:
        file_rep (dict): File data representation
        file_service (FileService): File service for interacting w/ filesystems

    Returns:
        Any: Unserialize file object

    """

    file_type = get_file_from_serializer_string(file_rep["file_type_string"])
    file_result = file_type(**file_rep)

    return file_result.read(file_service=file_service)
