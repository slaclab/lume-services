from prefect import task, Flow
from prefect.storage import Module
from lume_services.files import TextFile
import logging

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)


@task
def failure_task():
    assert 1 == 2



with Flow("flow1", storage=Module(__name__)) as flow:
    failure_task()