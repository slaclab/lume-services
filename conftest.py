import pytest
import os


def pytest_addoption(parser):
    parser.addini("mysql_host", default="127.0.0.1", help="MySQL host")
    parser.addini("mysql_port", default=3306, help="MySQL port")
    parser.addini("mysql_user", default="root", help="MySQL user")
    parser.addini("mysql_password", default="root", help="MySQL password")
    parser.addini(name="mysql_dbname", help="Mysql database name", default="test")
    parser.addini(name="mysql_params", help="MySQL params", default="")
    parser.addini("mysql_database", default="model_db", help="Model database name")
    parser.addini("mysql_poolsize", default=1, help="MySQL client poolsize")
    parser.addini(name="mysql_mysqld", help="mysqld command", default="mysqld")

    parser.addini("mongodb_host", default="127.0.0.1", help="MySQL host")
    parser.addini("mongodb_port", default=3306, help="MySQL port")
    parser.addini("mongodb_user", default="root", help="MySQL user")
    parser.addini("mongodb_password", default="root", help="MySQL password")
    parser.addini(name="mongodb_dbname", help="Mysql database name", default="test")

    parser.addini(
        name="mysql_mysqld_safe", help="mysqld safe command", default="mysqld_safe"
    )
    parser.addini(name="mysql_admin", help="mysql admin command", default="mysqladmin")
    parser.addini(
        name="mysql_logsdir",
        help="Add log directory",
    )
    parser.addini(
        name="mysql_install_db",
        help="Installation path",
        default="mysql_install_db",
    )


@pytest.fixture(scope="session", autouse=True)
def mysql_user(request):
    user = request.config.getini("mysql_user")
    os.environ["PYTEST_MYSQL_USER"] = user
    return user


@pytest.fixture(scope="session", autouse=True)
def mysql_password(request):
    user = request.config.getini("mysql_password")
    os.environ["PYTEST_MYSQL_PASSWORD"] = user
    return user


from glob import glob


def refactor(string: str) -> str:
    return string.replace("/", ".").replace("\\", ".").replace(".py", "")


pytest_plugins = [
    refactor(fixture)
    for fixture in glob("lume_services/tests/fixtures/**/*.py", recursive=True)
    if "__" not in fixture
]
