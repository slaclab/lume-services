from prefect import task, Flow
from lume_services.tasks import configure_lume_services
import logging

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)


@task(name="check_text_equivalence")
def check_text_equivalence(text1, text2):
    return text1 == text2


with Flow("flow3") as flow:
    configure = configure_lume_services()
    text1 = "text1"
    text2 = "text2"

    equivalence = check_text_equivalence(text1, text2)
