import pytest
from lume_services.services.results import (
    ResultsDBService,
    MongodbResultsDB,
    MongodbResultsDBConfig,
)
from pymongo import MongoClient

from lume_services.results import get_collections
from lume_services.tests.fixtures.docker import *  # noqa: F403, F401

import logging

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def mongodb_config(
    mongodb_host, mongodb_port, mongodb_database, mongodb_user, mongodb_password
):
    return MongodbResultsDBConfig(
        host=mongodb_host,
        port=mongodb_port,
        username=mongodb_user,
        password=mongodb_password,
        database=mongodb_database,
    )


def is_database_ready(docker_ip, mongodb_config):
    try:
        MongoClient(
            **mongodb_config.dict(by_alias=True, exclude_none=True),
            password=mongodb_config.password.get_secret_value(),
            connectTimeoutMS=20000,
            connect=True
        )
        return True

    except Exception as e:
        logger.error(e)
        return False


@pytest.fixture(scope="session", autouse=True)
def mongodb_server(docker_ip, docker_services, mongodb_config):
    docker_services.wait_until_responsive(
        timeout=40.0,
        pause=0.1,
        check=lambda: is_database_ready(docker_ip, mongodb_config),
    )
    return True


@pytest.fixture(scope="session", autouse=True)
def mongodb_results_db(mongodb_config, mongodb_server):
    return MongodbResultsDB(mongodb_config)


@pytest.fixture(scope="session", autouse=True)
def results_db_service(mongodb_results_db, mongodb_database, mongodb_server):

    collections = get_collections()
    mongodb_results_db.configure(collections=collections)

    results_db_service = ResultsDBService(results_db=mongodb_results_db)

    yield results_db_service

    with results_db_service._results_db.client() as client:
        client.drop_database(mongodb_database)
