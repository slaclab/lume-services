import pytest

from lume_services.services.data.results.results_service import (
    ResultsServiceConfig,
)
from lume_services.context import Context, LUMEServicesConfig


@pytest.fixture(scope="module")
def context(
    mongodb_service,
    mysql_service,
    mysql_config,
    mongodb_config,
    model_docs,
    file_service,
):
    # don't use factory here because want to use pytest fixture management

    results_service_config = ResultsServiceConfig(
        model_docs=model_docs,
    )

    config = LUMEServicesConfig(
        results_service_config=results_service_config,
        model_db_service_config=mysql_config,
        results_db_service_config=mongodb_config,
    )

    context = Context(
        results_db_service=mongodb_service,
        model_db_service=mysql_service,
        file_service=file_service,
    )

    context.config.from_pydantic(config)

    return context
