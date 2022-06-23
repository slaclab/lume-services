import logging
from dependency_injector.wiring import Provide
from prefect import task
from typing import Any

from lume_services.context import Context
from lume_services.services.data.results import ResultsDB
from lume_services.services.data.files import FileService
from prefect.engine.results import PrefectResult

from lume_services.data.files import get_file_from_serializer_string, File
from lume_services.data.results import get_result_from_string, Result

logger = logging.getLogger(__name__)


@task(log_stdout=True, result=PrefectResult())  # SAVE W/ PREFECT RESULT
def save_db_result_task(
    result: Result, results_db_service: ResultsDB = Provide[Context.results_db_service]
) -> dict:
    """Insert result into the results database service. Creates a PrefectResult that
    contains minimal representative information for reconstruction.

    Args:
        result (Result): Result object to save
        results_db_service (ResultsDB): Results database service


    Returns:
        dict: Unique representation for collecting results.

    """

    result.insert(results_db_service=results_db_service)
    return result.unique_rep()


@task(log_stdout=True)
def load_db_result_task(
    result_rep, results_db_service: ResultsDB = Provide[Context.results_db_service]
) -> Result:
    """

    Args:
        result_rep (dict): Result representation containing result_type_string and query
        results_db_service (ResultsDB): Results database service

    Returns:
        Result

    Note: requires instructions for accessing attributtes


    """
    result_type = get_result_from_string(result_rep["result_type_string"])
    result = result_type.load_from_query(
        result_rep["query"], results_db_service=results_db_service
    )

    return result


@task()
def load_file_task(
    file_rep, file_service: FileService = Provide[Context.file_service]
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


@task(log_stdout=True, result=PrefectResult())
def save_file_task(
    file: File, file_service: FileService = Provide[Context.file_service]
):
    """Save a file

    Args:
        file (File): File object
        file_service (FileService): File service for interacting w/ filesystems

    Returns:
        dict: Loaded file type

    """
    file.write(file_service=file_service)
    return file.jsonable_dict()
