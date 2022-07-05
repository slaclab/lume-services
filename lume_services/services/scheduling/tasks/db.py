import logging
from dependency_injector.wiring import Provide, inject
from prefect import task

from lume_services.config import Context
from lume_services.services.data.results import ResultsDB
from prefect.engine.results import PrefectResult

from lume_services.data.results import get_result_from_string, Result

logger = logging.getLogger(__name__)


@inject
@task(log_stdout=True, result=PrefectResult())
def save_db_result(
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


@inject
@task(log_stdout=True)
def load_db_result(
    result_rep: dict,
    results_db_service: ResultsDB = Provide[Context.results_db_service],
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
