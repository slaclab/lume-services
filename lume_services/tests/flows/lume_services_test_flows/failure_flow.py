from prefect import task, Flow
import logging

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)


@task
def failure_task():
    assert 1 == 2


with Flow("failure_flow") as flow:
    failure_task()
