import pytest
import logging
from sqlalchemy import create_engine

from lume_services.services.models.db import ModelDB, ModelDBConfig
from lume_services.services.models.service import ModelDBService

from lume_services.tests.fixtures.docker import *  # noqa: F403, F401

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def mysql_config(
    mysql_user, mysql_password, mysql_host, mysql_port, mysql_database, mysql_pool_size
):

    return ModelDBConfig(
        user=mysql_user,
        password=mysql_password,
        host=mysql_host,
        port=mysql_port,
        database=mysql_database,
        connection={"pool_size": mysql_pool_size},
    )


@pytest.mark.usefixtures("docker_services")
@pytest.fixture(scope="session", autouse=True)
def mysql_service(mysql_config):
    mysql_service = ModelDB(mysql_config)
    return mysql_service


@pytest.mark.usefixtures("docker_services")
@pytest.fixture(scope="module", autouse=True)
def model_db_service(mysql_service, mysql_database, base_mysql_uri):

    engine = create_engine(base_mysql_uri, pool_size=1)
    with engine.connect() as connection:
        connection.execute(f"CREATE DATABASE IF NOT EXISTS {mysql_database};")

    model_db_service = ModelDBService(mysql_service)
    model_db_service.apply_schema()

    # set up database
    yield model_db_service

    with engine.connect() as connection:
        connection.execute(f"DROP DATABASE {mysql_database};")
