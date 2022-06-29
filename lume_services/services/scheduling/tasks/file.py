import logging
from dependency_injector.wiring import Provide
from prefect import task
from typing import Any

from lume_services.context import Context
from lume_services.services.data.files import FileService
from prefect.engine.results import PrefectResult

from lume_services.data.files import get_file_from_serializer_string

logger = logging.getLogger(__name__)


@task(log_stdout=True, result=PrefectResult())
def save_file_task(
    obj: Any,
    filename: str,
    file_system_identifier: str,
    file_type: type,
    file_service: FileService = Provide[Context.file_service],
):
    """Save a file

    Args:
        obj (Any): Object to be saved
        filename (str): File path to save
        file_system_identifier (str): String identifier for filesystem configured with
            File Service
        file_type (type): Type of file to save as
        file_service (FileService): File service for interacting w/ filesystems

    Returns:
        dict: Loaded file type

    """
    file = file_type(
        obj=obj, file_system_identifier=file_system_identifier, filename=filename
    )
    file.write(file_service=file_service)
    return file.jsonable_dict()


@task()
def load_file_task(
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
