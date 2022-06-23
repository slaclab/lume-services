import logging
from dependency_injector.wiring import Provide
from prefect import task
import json

from lume_services.context import Context
from lume_services.services.data.results import ResultsDB
from lume_services.services.data.files import FileService

from lume_services.data.files import get_file_from_serializer_string
from lume_services.data.results import get_result_from_string

logger = logging.getLogger(__name__)


@task()
def load_db_result_task(
    result_json_rep, results_db_service: ResultsDB = Provide[Context.results_db_service]
):

    json_loaded = json.loads(result_json_rep)
    result_type = get_result_from_string(json_loaded["result_type_string"])

    result = result_type.parse_raw(result_json_rep)

    return result.load_result(results_db_service=results_db_service)


@task()  # SAVE W/ PREFECT RESULT
def save_db_result_task(
    result_json_rep, results_db_service: ResultsDB = Provide[Context.results_db_service]
):
    json_loaded = json.loads(result_json_rep)
    result_type = get_result_from_string(json_loaded["result_type_string"])

    result = result_type.parse_raw(result_json_rep)

    return result.load_result(results_db_service=results_db_service)


@task()
def load_file_task(
    file_json_rep, file_service: FileService = Provide[Context.file_service]
):

    json_loaded = json.loads(file_json_rep)
    result_type = get_file_from_serializer_string(json_loaded["serializer_type"])

    file_result = result_type.parse_raw(file_json_rep)

    return file_result.read(file_service=file_service)


@task()  # SAVE W/ PREFECT RESULT
def save_file_task(
    file, results_db_service: ResultsDB = Provide[Context.results_db_service]
):
    ...
