import logging
from dependency_injector.wiring import Provide
from prefect import task
import json

from lume_services.context import Context
from lume_services.services.data.files import FileService

from lume_services.data.file import get_file_from_serializer_string

logger = logging.getLogger(__name__)


@task()
def load_file_task(
    file_json_rep, file_service: FileService = Provide[Context.file_service]
):

    json_loaded = json.loads(file_json_rep)
    result_type = get_file_from_serializer_string(json_loaded["serializer_type"])

    file_result = result_type.parse_raw(file_json_rep)

    return file_result.read(file_service=file_service)
