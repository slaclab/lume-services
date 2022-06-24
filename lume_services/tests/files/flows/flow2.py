from prefect import task, Flow, Parameter
from lume_services.services.scheduling.tasks import load_file_task, save_db_result_task
from lume_services.data.results import Result


@task
def format_result(text):
    # get test flow id from prefect context
    result = Result(
        inputs={"input1": text},
        outputs={},
    )
    return result


with Flow("flow2") as flow2:
    file_rep = Parameter("file_rep")
    # load file
    loaded_text = load_file_task(file_rep)
    result = format_result(loaded_text)
    db_result = save_db_result_task(result)
