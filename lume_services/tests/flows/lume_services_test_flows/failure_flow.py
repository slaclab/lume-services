from prefect import task, Flow
from prefect.storage import Module
import logging

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)


@task
def failure_task():
    assert 1 == 2


with Flow(
    "failure_flow", storage=Module(__name__.replace("lume_services.tests.flows.", ""))
) as flow:
    failure_task()
