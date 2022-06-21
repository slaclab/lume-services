import pytest
import os
from sqlalchemy import create_engine
import pymysql
import logging

from lume_services.services.data.model.db.mysql import MySQLConfig, MySQLService
from lume_services.services.data.model.model_service import ModelService


logger = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def mysql_host(request):
    return request.config.getini("mysql_host")


@pytest.fixture(scope="session", autouse=True)
def mysql_port(request):
    port = request.config.getini("mysql_port")
    os.environ["PYTEST_MYSQL_PORT"] = port
    return int(port)


@pytest.fixture(scope="session", autouse=True)
def mysql_database(request):
    return request.config.getini("mysql_database")


@pytest.fixture(scope="session", autouse=True)
def mysql_pool_size(request):
    return int(request.config.getini("mysql_poolsize"))


@pytest.fixture(scope="session", autouse=True)
def base_mysql_uri(mysql_user, mysql_password, mysql_host, mysql_port):
    return f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}"


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