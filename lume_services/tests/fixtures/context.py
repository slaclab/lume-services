import pytest
from lume_services.config import (
    LUMEServicesSettings,
    configure,
    context as config_context,
)


@pytest.fixture(scope="session")
def lume_services_settings(mysql_config, mongodb_config):

    settings = LUMEServicesSettings(
        model_db=mysql_config,
        results_db=mongodb_config,
    )
    return settings


@pytest.fixture(scope="session")
def context(lume_services_settings):

    configure(lume_services_settings)
    return config_context
