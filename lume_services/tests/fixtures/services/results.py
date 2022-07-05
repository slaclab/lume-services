import pytest
from datetime import datetime
from lume_services.data.files import HDF5File, ImageFile
from lume_services.services.data.results import (
    ResultsDBService,
    MongodbResultsDB,
    MongodbResultsDBConfig,
)
from pymongo import MongoClient

from lume_services.data.results import get_collections, Result, ImpactResult
from lume_services.tests.files import SAMPLE_IMAGE_FILE, SAMPLE_IMPACT_ARCHIVE

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
        user=mongodb_user,
        password=mongodb_password,
        database=mongodb_database,
    )


def is_database_ready(docker_ip, mongodb_config):
    try:
        MongoClient(
            mongodb_config.uri, **mongodb_config.dict(exclude_none=True), connect=True
        )
        return True
    except Exception as e:
        logger.error(e)
        return False


@pytest.fixture(scope="session", autouse=True)
def mongodb_server(docker_ip, docker_services, mongodb_config):
    docker_services.wait_until_responsive(
        timeout=20.0,
        pause=0.1,
        check=lambda: is_database_ready(docker_ip, mongodb_config),
    )
    return


@pytest.fixture(scope="session", autouse=True)
def mongodb_results_db(mongodb_config, mongodb_server):
    return MongodbResultsDB(mongodb_config)


@pytest.fixture(scope="class", autouse=True)
def results_db_service(mongodb_results_db, mongodb_database, mongodb_server):

    collections = get_collections()
    mongodb_results_db.configure(collections=collections)

    results_db_service = ResultsDBService(results_db=mongodb_results_db)

    yield results_db_service

    with results_db_service._results_db.client() as client:
        client.drop_database(mongodb_database)


@pytest.fixture(scope="session", autouse=True)
def generic_result():
    return Result(
        flow_id="test_flow_id",
        inputs={"input1": 2.0, "input2": [1, 2, 3, 4, 5]},
        outputs={
            "output1": 2.0,
            "output2": [1, 2, 3, 4, 5],
        },
    )


@pytest.fixture(scope="session", autouse=True)
def impact_result():
    return ImpactResult(
        flow_id="test_flow_id",
        inputs={"input1": 2.0, "input2": [1, 2, 3, 4, 5], "input3": "my_file.txt"},
        outputs={
            "output1": 2.0,
            "output2": [1, 2, 3, 4, 5],
            "output3": "my_file.txt",
        },
        plot_file=ImageFile(filename=SAMPLE_IMAGE_FILE, filesystem_identifier="local"),
        archive=HDF5File(filename=SAMPLE_IMPACT_ARCHIVE, filesystem_identifier="local"),
        pv_collection_isotime=datetime.now(),
        config={"config1": 1, "config2": 2},
    )
