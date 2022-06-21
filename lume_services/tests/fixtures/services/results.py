import pytest
import mongomock
from mongoengine import connect

from lume_services.services.data.results.db import MongodbService, MongoDBConfig
from lume_services.services.data.results.results_service import (
    ResultsService,
)


@pytest.fixture(scope="session", autouse=True)
def mongodb_host(request):
    return request.config.getini("mysql_host")


@pytest.fixture(scope="session", autouse=True)
def mongodb_port(request):
    port = request.config.getini("mongodb_port")
    return int(port)


@pytest.fixture(scope="session", autouse=True)
def mongodb_database(request):
    return request.config.getini("mongodb_database")


@pytest.fixture(scope="session", autouse=True)
def mongodb_config(mongodb_host, mongodb_port, mongodb_database):
    uri = f"mongomock://{mongodb_host}@{mongodb_port}"
    return MongoDBConfig(uri=uri, database=mongodb_database)


@mongomock.patch(servers=(("localhost", 27017),))
@pytest.fixture(scope="module", autouse=True)
def mongodb_service(mongodb_config):
    return MongodbService(mongodb_config)


@pytest.fixture(scope="module", autouse=True)
def results_service(mongodb_service):

    results_service = ResultsService(mongodb_service)

    yield results_service

    cxn = connect("test", host="mongomock://localhost")
    cxn.drop_database("test")
