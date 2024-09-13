from prefect import task, Flow
from lume_services.tasks import configure_lume_services, SaveFile
from lume_services.files import TextFile
import logging

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)


@task
def append_text(text1, text2):
    return text1 + text2


save_file = SaveFile(name="save_text_file", task_run_name="save_text_file")

with Flow("flow1") as flow:
    text1 = "text1"
    text2 = "text2"
    filename = "filename"
    filesystem_identifier = "filesystem_identifier"
    configure = configure_lume_services()
    new_text = append_text(text1, text2)
    file = save_file(
        obj=new_text,
        file_type=TextFile,
        filename=filename,
        filesystem_identifier=filesystem_identifier,
    )
    file.set_upstream(configure)
