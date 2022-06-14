import pytest
from sqlalchemy import create_engine
from datetime import datetime
import mongomock
import pymysql
import logging
from mongoengine import connect

from lume_services.data.model.db.mysql import MySQLConfig, MySQLService
from lume_services.data.model.model_service import ModelService
from lume_services.data.results.db.db_service import DBServiceConfig
from lume_services.data.results.db.mongodb.service import MongodbService
from lume_services.data.results.results_service import (
    ResultsService,
    ResultsServiceConfig,
)

from lume_services.data.file.systems.local import LocalFilesystem
from lume_services.data.file.service import FileService

from lume_services.data.results.db.mongodb.models import ModelDocs as MongoDBModelDocs

from lume_services.context import Context, LUMEServicesConfig

from lume.serializers.base import SerializerBase


logger = logging.getLogger(__name__)


def is_database_ready(docker_ip, mysql_user, mysql_password):
    try:
        pymysql.connect(
            host=docker_ip,
            user=mysql_user,
            password=mysql_password,
        )
        return True
    except Exception as e:
        logger.error(e)
        return False


@pytest.fixture(scope="session")
def mysql_server(docker_ip, docker_services, mysql_user, mysql_password):
    docker_services.wait_until_responsive(
        timeout=10.0,
        pause=0.1,
        check=lambda: is_database_ready(docker_ip, mysql_user, mysql_password),
    )
    return


def test_mysql(
    mysql_user, mysql_host, mysql_password, docker_ip, docker_services, mysql_server
):
    """Ensure that HTTP service is up and responsive."""

    port = docker_services.port_for("mysql", 3306)

    connect_str = (
        f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{str(port)}"
    )
    engine = create_engine(connect_str)

    conn = engine.connect()
    conn.close()


@pytest.fixture(scope="session", autouse=True)
def mysql_config(base_mysql_uri, mysql_database, mysql_pool_size):

    return MySQLConfig(
        db_uri=f"{base_mysql_uri}/{mysql_database}",
        pool_size=mysql_pool_size,
    )


@pytest.mark.usefixtures("mysql_server")
@pytest.fixture(scope="module", autouse=True)
def mysql_service(mysql_config):
    mysql_service = MySQLService(mysql_config)
    return mysql_service


@pytest.fixture(scope="session")
def model_docs():
    return MongoDBModelDocs


@pytest.mark.usefixtures("mysql_server")
@pytest.fixture(scope="module", autouse=True)
def model_service(mysql_service, mysql_database, base_mysql_uri):

    engine = create_engine(base_mysql_uri, pool_size=1)
    with engine.connect() as connection:
        connection.execute(f"CREATE DATABASE IF NOT EXISTS {mysql_database};")

    model_service = ModelService(mysql_service)
    model_service.apply_schema()

    # set up database
    yield model_service

    with engine.connect() as connection:
        connection.execute(f"DROP DATABASE {mysql_database};")


class MongomockResultsDBConfig(DBServiceConfig):
    host: str = "mongomock://localhost"
    db: str = "test"
    port: int = 27017


@pytest.fixture(scope="session", autouse=True)
def mongodb_config():
    return MongomockResultsDBConfig()


@mongomock.patch(servers=(("localhost", 27017),))
@pytest.fixture(scope="module", autouse=True)
def mongodb_service(mongodb_config):
    return MongodbService(mongodb_config)


@pytest.fixture(scope="module", autouse=True)
def results_service(mongodb_service, model_docs):

    results_service = ResultsService(mongodb_service, model_docs)

    yield results_service

    cxn = connect("test", host="mongomock://localhost")
    cxn.drop_database("test")


@pytest.fixture(scope="module", autouse=True)
def local_filesystem_handler():
    return LocalFilesystem()


class TextSerializer(SerializerBase):
    def serialize(self, filename, text):

        with open(filename, "w") as f:
            f.write(text)

    @classmethod
    def deserialize(cls, filename):

        text = ""

        with open(filename, "r") as f:
            text = f.read()

        return text


@pytest.fixture(scope="module")
def file_service(local_filesystem_handler):
    filesystems = [local_filesystem_handler]

    return FileService(filesystems)


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
