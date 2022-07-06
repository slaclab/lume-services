from prefect import task, Flow, Parameter
from prefect.storage import Module
from lume_services.services.scheduling.tasks import (
    load_file,
    save_db_result,
    configure_services,
)

from lume_services.data.results import Result
import logging

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)


@task
def format_result(text):
    # get test flow id from prefect context
    result = Result(
        inputs={"input1": text},
        outputs={},
    )
    return result


with Flow("flow2", storage=Module(__name__)) as flow2:
    file_rep = Parameter("file_rep")
    # load file
    configure_services()
    loaded_text = load_file(file_rep)
    result = format_result(loaded_text)
    db_result = save_db_result(result)
