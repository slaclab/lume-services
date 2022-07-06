from prefect import task, Flow, Parameter
from prefect.storage import Module

from lume_services.services.scheduling.tasks import configure_services
import logging

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)


@task
def check_text_equivalence(text1, text2):
    assert text1 == text2


with Flow("flow3", storage=Module(__name__)) as flow3:
    text1 = Parameter("text1")
    text2 = Parameter("text2")
    configure_services()

    check_text_equivalence(text1, text2)
