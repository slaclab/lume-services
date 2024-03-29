from prefect import task, Flow, Parameter
from prefect.storage import Module
from lume_services.tasks import (
    LoadFile,
    SaveDBResult,
    configure_lume_services,
)

from lume_services.results import Result
import logging

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)


@task
def format_result(text):
    # get test flow id from prefect context
    result = Result(
        inputs={"input1": text},
        outputs={"output1": text},
    )
    return result


load_file = LoadFile()
save_db_result = SaveDBResult()

with Flow(
    "flow2", storage=Module(__name__.replace("lume_services.tests.flows.", ""))
) as flow:
    file_rep = Parameter("file_rep")
    # load file
    configure = configure_lume_services()
    loaded_text = load_file(file_rep)
    result = format_result(loaded_text)
    db_result = save_db_result(result)

    # set configure upstreams
    loaded_text.set_upstream(configure)
    db_result.set_upstream(configure)
