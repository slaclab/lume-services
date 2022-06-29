from prefect import task, Flow, Parameter
from prefect.engine.results import PrefectResult
from lume_services.services.scheduling.tasks.file import save_file_task, load_file_task
from lume_services.data.files import TextFile


@task(result=PrefectResult())
def append_text(text1, text2):
    return text1 + text2


with Flow("flow1") as flow1:
    text1 = Parameter("text1")
    text2 = Parameter("text2")
    filename = Parameter("filename")
    file_system_identifier = Parameter("file_system_identifier")
    new_text = append_text(text1, text2)
    file = save_file_task(
        obj=new_text,
        file_type=TextFile,
        filename=filename,
        file_system_identifier=file_system_identifier,
    )

with Flow("flow2") as flow2:
    file_rep = Parameter("file_rep")
    loaded_text = load_file_task(file_rep)
