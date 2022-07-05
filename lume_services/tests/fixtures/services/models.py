import pytest
import pymysql
import logging
from sqlalchemy import create_engine

from lume_services.services.data.models.db.mysql import MySQLModelDBConfig, MySQLModelDB
from lume_services.services.data.models.model_service import ModelDBService

from lume_services.tests.fixtures.config import *  # noqa: F403, F401
from lume_services.tests.fixtures.docker import *  # noqa: F403, F401

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


@pytest.fixture(scope="session", autouse=True)
def mysql_server(docker_ip, docker_services, mysql_user, mysql_password):
    docker_services.wait_until_responsive(
        timeout=20.0,
        pause=0.1,
        check=lambda: is_database_ready(docker_ip, mysql_user, mysql_password),
    )
    return


@pytest.fixture(scope="session", autouse=True)
def mysql_config(
    mysql_user, mysql_password, mysql_host, mysql_port, mysql_database, mysql_pool_size
):

    return MySQLModelDBConfig(
        user=mysql_user,
        password=mysql_password,
        host=mysql_host,
        port=mysql_port,
        database=mysql_database,
        pool_size=mysql_pool_size,
    )


@pytest.mark.usefixtures("mysql_server")
@pytest.fixture(scope="module", autouse=True)
def mysql_service(mysql_config):
    mysql_service = MySQLModelDB(mysql_config)
    return mysql_service


@pytest.mark.usefixtures("mysql_server")
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
