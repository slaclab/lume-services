import pytest
import os


def pytest_addoption(parser):
    parser.addini("mysql_host", default="127.0.0.1", help="MySQL host")
    parser.addini("mysql_port", default=3306, help="MySQL port")
    parser.addini("mysql_user", default="root", help="MySQL user")
    parser.addini("mysql_password", default="root", help="MySQL password")
    parser.addini(name="mysql_dbname", help="Mysql database name", default="test")
    parser.addini("mysql_database", default="model_db", help="Model database name")
    parser.addini("mysql_poolsize", default=1, help="MySQL client poolsize")

    parser.addini("mongodb_host", default="127.0.0.1", help="MySQL host")
    parser.addini("mongodb_port", default=3306, help="MySQL port")
    parser.addini("mongodb_user", default="root", help="MySQL user")
    parser.addini("mongodb_password", default="root", help="MySQL password")
    parser.addini(name="mongodb_dbname", help="Mysql database name", default="test")

    # prefect
    parser.addini(name="postgres_db", help="Prefect postgres db", default="prefect_db")
    parser.addini(
        name="postgres_user", help="Prefect postgres user", default="prefect_user"
    )
    parser.addini(
        name="postgres_password",
        help="Prefect postgres password",
        default="prefect_password",
    )
    parser.addini(name="apollo_host_port", help="Prefect apollo api port", default=4200)
    parser.addini(
        name="hasura_host_port", help="Prefect hasura host port", default=3000
    )
    parser.addini(
        name="postgres_host_port", help="Prefect postgres host port", default=3000
    )
    parser.addini(
        name="graphql_host_port", help="Prefect graphql host port", default=4201
    )


@pytest.fixture(scope="session", autouse=True)
def rootdir(request):
    rootdir = request.config.rootpath
    os.environ["LUME_SERVICES_ROOTDIR"] = str(rootdir)
    return rootdir


from glob import glob


def refactor(string: str) -> str:
    return string.replace("/", ".").replace("\\", ".").replace(".py", "")


pytest_plugins = [
    refactor(fixture)
    for fixture in glob("lume_services/tests/fixtures/**/*.py", recursive=True)
    if "__" not in fixture
]
