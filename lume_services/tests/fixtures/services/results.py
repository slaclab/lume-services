import pytest
from lume_services.services.results import (
    MongodbResultsDB,
    MongodbResultsDBConfig,
    ResultsDBService,
)

from lume_services.tests.fixtures.docker import *  # noqa: F403, F401
from lume_services.results import get_collections

import logging

logger = logging.getLogger(__name__)


@pytest.mark.usefixtures("docker_services")
@pytest.fixture(scope="session", autouse=True)
def mongodb_results_db(
    mongodb_host, mongodb_port, mongodb_user, mongodb_password, mongodb_database
):
    mongodb_config = MongodbResultsDBConfig(
        host=mongodb_host,
        port=mongodb_port,
        username=mongodb_user,
        password=mongodb_password,
        database=mongodb_database,
    )
    return MongodbResultsDB(mongodb_config)


@pytest.mark.usefixtures("docker_services")
@pytest.fixture(scope="session", autouse=True)
def results_db_service(mongodb_results_db, mongodb_database):

    collections = get_collections()
    mongodb_results_db.configure(collections=collections)

    results_db_service = ResultsDBService(results_db=mongodb_results_db)

    yield results_db_service

    with results_db_service._results_db.client() as client:
        client.drop_database(mongodb_database)
