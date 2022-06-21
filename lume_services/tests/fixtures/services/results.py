import pytest
import mongomock
from datetime import datetime

from lume_services.services.data.results import (
    MongodbResultsDBServiceConfig,
    MongodbResultsDBService,
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
    return request.config.getini("mongodb_dbname")


@pytest.fixture(scope="session", autouse=True)
def mongodb_config(mongodb_host, mongodb_port, mongodb_database):
    uri = f"mongomock://{mongodb_host}@{mongodb_port}"
    return MongodbResultsDBServiceConfig(uri=uri, database=mongodb_database)


@mongomock.patch(servers=(("localhost", 27017),))
@pytest.fixture(scope="module", autouse=True)
def mongodb_service(mongodb_config):
    return MongodbResultsDBService(mongodb_config)


@pytest.fixture(scope="module", autouse=True)
def results_service(mongodb_service):

    yield mongodb_service

    with mongodb_service.db_service.connection() as client:
        client.drop_database("test")


@pytest.fixture(scope="session", autouse=True)
def test_generic_result_document():
    return {
        "flow_id": "test_flow_id",
        "inputs": {"input1": 2.0, "input2": [1, 2, 3, 4, 5], "input3": "my_file.txt"},
        "outputs": {
            "output1": 2.0,
            "output2": [1, 2, 3, 4, 5],
            "ouptut3": "my_file.txt",
        },
    }


@pytest.fixture(scope="module", autouse=True)
def test_impact_result_document():
    return {
        "flow_id": "test_flow_id",
        "inputs": {"input1": 2.0, "input2": [1, 2, 3, 4, 5], "input3": "my_file.txt"},
        "outputs": {
            "output1": 2.0,
            "output2": [1, 2, 3, 4, 5],
            "ouptut3": "my_file.txt",
        },
        "plot_file": "my_plot_file.txt",
        "archive": "archive_file.txt",
        "pv_collection_isotime": datetime.now(),
        "config": {"config1": 1, "config2": 2},
    }
