import pytest

from lume_services.context import Context, LUMEServicesConfig


@pytest.fixture(scope="class")
def context(
    results_db_service,
    mysql_service,
    mysql_config,
    mongodb_config,
    file_service,
):
    # don't use factory here because want to use pytest fixture management

    config = LUMEServicesConfig(
        model_db_service_config=mysql_config,
        results_db_service_config=mongodb_config,
    )

    context = Context(
        results_db_service=results_db_service,
        model_db_service=mysql_service,
        file_service=file_service,
    )

    context.config.from_pydantic(config)

    return context
