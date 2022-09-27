from prefect import task, Flow, Parameter
from prefect.storage import Module
from prefect.engine.results import PrefectResult
from lume_services.tasks import configure_lume_services
import logging

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)


@task(
    name="check_text_equivalence",
    result=PrefectResult(location="check_equivalence.prefect"),
)
def check_text_equivalence(text1, text2):
    return text1 == text2


with Flow(
    "flow3", storage=Module(__name__.replace("lume_services.tests.flows.", ""))
) as flow:

    configure = configure_lume_services()
    text1 = Parameter("text1")
    text2 = Parameter("text2")

    equivalence = check_text_equivalence(text1, text2)
