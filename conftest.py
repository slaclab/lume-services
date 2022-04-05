import pytest 
from pytest_mysql import factories
from sqlalchemy import create_engine
from string import Template

from lume_services.data.model.db.mysql import MySQLConfig, MySQLService
from lume_services.data.model.model_db_service import ModelDBService


mysql_server = factories.mysql_proc()


def pytest_addoption(parser):

    parser.addini(
        "mysql_user", default="root", help="MySQL user"
    )

    parser.addini(
        "mysql_database", default="model_db", help="Model database name"
    )

    parser.addini(
        "mysql_poolsize", default=1, help="MySQL client poolsize"
    )


@pytest.fixture(scope="session", autouse=True)
def mysql_user(request):
    return request.config.getini("mysql_user")

@pytest.fixture(scope="session", autouse=True)
def mysql_host(request):
    return request.config.getini("mysql_host")


@pytest.fixture(scope="session", autouse=True)
def mysql_port(request):
    return int(request.config.getini("mysql_port"))


@pytest.fixture(scope="session", autouse=True)
def mysql_database(request):
    return request.config.getini("mysql_database")


@pytest.fixture(scope="session", autouse=True)
def mysql_pool_size(request):
    return int(request.config.getini("mysql_poolsize"))


@pytest.fixture(scope="session", autouse=True)
def base_db_uri(mysql_user, mysql_host, mysql_port):
    return Template("mysql+pymysql://${user}:@${host}:${port}").substitute(user=mysql_user, host=mysql_host, port=mysql_port)


@pytest.fixture(scope="session", autouse=True)
def mysql_config(mysql_user, mysql_host, mysql_port, mysql_database, mysql_pool_size):

    db_uri = Template("mysql+pymysql://${user}:@${host}:${port}/${database}").substitute(user=mysql_user, host=mysql_host, port=mysql_port, database=mysql_database)

    return MySQLConfig(
        db_uri=db_uri,
        pool_size=mysql_pool_size,
    )


@pytest.mark.usefixtures("mysql_proc")
@pytest.fixture(scope="module", autouse=True)
def mysql_service(mysql_config):
    mysql_service = MySQLService(mysql_config)
    return mysql_service



@pytest.mark.usefixtures("mysql_proc")
@pytest.fixture(scope="module", autouse=True)
def model_db_service(mysql_service, mysql_database, base_db_uri, mysql_proc):

    # start the mysql process if not started
    if not mysql_proc.running():
        mysql_proc.start()

    engine = create_engine(base_db_uri, pool_size=1)
    with engine.connect() as connection:
        connection.execute("CREATE DATABASE IF NOT EXISTS model_db;")

    model_db_service = ModelDBService(mysql_service)
    model_db_service.apply_schema()

    # set up database
    yield model_db_service

    with engine.connect() as connection:
        connection.execute(f"DROP DATABASE {mysql_database};")



"""

@pytest.fixture(scope="session", autouse=True)
def mongodb_results_db():
    ...

"""