from prefect import task, Flow, Parameter
from prefect.storage import Module
from lume_services.tasks import configure_lume_services, SaveFile
from lume_services.files import TextFile
import logging

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)


@task
def append_text(text1, text2):
    return text1 + text2


save_file = SaveFile(name="save_text_file", task_run_name="save_text_file")

with Flow(
    "flow1", storage=Module(__name__.replace("lume_services.tests.flows.", ""))
) as flow:
    text1 = Parameter("text1")
    text2 = Parameter("text2")
    filename = Parameter("filename")
    filesystem_identifier = Parameter("filesystem_identifier")
    configure = configure_lume_services()
    new_text = append_text(text1, text2)
    file = save_file(
        obj=new_text,
        file_type=TextFile,
        filename=filename,
        filesystem_identifier=filesystem_identifier,
    )
    file.set_upstream(configure)
