import pytest
import os
import docker


from lume_services.services.files.filesystems import (
    LocalFilesystem,
    MountedFilesystem,
)


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
    parser.addini("mongodb_password", default="password", help="MySQL password")
    parser.addini(name="mongodb_database", help="Mysql database name", default="test")

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


@pytest.fixture(scope="session", autouse=True)
def mysql_host(request):
    host = request.config.getini("mysql_host")
    os.environ["LUME_MODEL_DB__HOST"] = host
    return host


@pytest.fixture(scope="session", autouse=True)
def mysql_user(request):
    user = request.config.getini("mysql_user")
    os.environ["LUME_MODEL_DB__USER"] = user
    return user


@pytest.fixture(scope="session", autouse=True)
def mysql_password(request):
    password = request.config.getini("mysql_password")
    os.environ["LUME_MODEL_DB__PASSWORD"] = password
    return password


@pytest.fixture(scope="session", autouse=True)
def mysql_port(request):
    port = request.config.getini("mysql_port")
    os.environ["LUME_MODEL_DB__PORT"] = port
    return int(port)


@pytest.fixture(scope="session", autouse=True)
def mysql_database(request):
    database = request.config.getini("mysql_database")
    os.environ["LUME_MODEL_DB__DATABASE"] = database
    return database


@pytest.fixture(scope="session", autouse=True)
def mysql_pool_size(request):
    pool_size = request.config.getini("mysql_poolsize")
    os.environ["LUME_MODEL_DB__CONNECTION__POOL_SIZE"] = pool_size
    return int(pool_size)


@pytest.fixture(scope="session", autouse=True)
def base_mysql_uri(mysql_user, mysql_password, mysql_host, mysql_port):
    return f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}"


## Prefect


@pytest.fixture(scope="session")
def apollo_host_port(request):
    port = request.config.getini("apollo_host_port")
    os.environ["APOLLO_HOST_PORT"] = port
    return port


@pytest.fixture(scope="session")
def hasura_host_port(request):
    port = request.config.getini("hasura_host_port")
    os.environ["HASURA_HOST_PORT"] = port
    return port


@pytest.fixture(scope="session")
def graphql_host_port(request):
    port = request.config.getini("graphql_host_port")
    os.environ["GRAPHQL_HOST_PORT"] = port
    return port


@pytest.fixture(scope="session")
def postgres_db(request):
    db = request.config.getini("postgres_db")
    os.environ["POSTGRES_DB"] = db
    return db


@pytest.fixture(scope="session")
def postgres_user(request):
    user = request.config.getini("postgres_user")
    os.environ["POSTGRES_USER"] = user
    return user


@pytest.fixture(scope="session")
def postgres_password(request):
    password = request.config.getini("postgres_password")
    os.environ["POSTGRES_PASSWORD"] = password
    return password


@pytest.fixture(scope="session")
def postgres_data_path(tmp_path_factory):
    temp_path = tmp_path_factory.mktemp("postgres_data_path")
    os.environ["POSTGRES_DATA_PATH"] = str(temp_path)
    return temp_path


@pytest.fixture(scope="session")
def prefect_api_str(apollo_host_port):
    return f"http://localhost:{apollo_host_port}"


@pytest.fixture(scope="session")
def graphql_api_str(apollo_host_port):
    return f"http://localhost:{apollo_host_port}/graphql"


## mongodb


@pytest.fixture(scope="session", autouse=True)
def mongodb_host(request):
    mongodb_host = request.config.getini("mongodb_host")
    os.environ["LUME_RESULTS_DB__HOST"] = mongodb_host
    return mongodb_host


@pytest.fixture(scope="session", autouse=True)
def mongodb_port(request):
    mongodb_port = request.config.getini("mongodb_port")
    os.environ["LUME_RESULTS_DB__PORT"] = mongodb_port
    return int(mongodb_port)


@pytest.fixture(scope="session", autouse=True)
def mongodb_user(request):
    mongodb_user = request.config.getini("mongodb_user")
    os.environ["LUME_RESULTS_DB__USERNAME"] = mongodb_user
    return mongodb_user


@pytest.fixture(scope="session", autouse=True)
def mongodb_password(request):
    mongodb_password = request.config.getini("mongodb_password")
    os.environ["LUME_RESULTS_DB__PASSWORD"] = mongodb_password
    return mongodb_password


@pytest.fixture(scope="session", autouse=True)
def mongodb_database(request):
    database = request.config.getini("mongodb_database")
    os.environ["LUME_RESULTS_DB__DATABASE"] = database
    return database


## Scheduling


## Filesystem
@pytest.fixture(scope="session")
def mount_path(tmp_path_factory):
    return str(tmp_path_factory.mktemp("mounted_dir"))


@pytest.fixture(scope="session", autouse=True)
def local_filesystem_handler():
    return LocalFilesystem()


@pytest.fixture(scope="session", autouse=True)
def mounted_filesystem_handler(mount_path):
    os.environ["LUME_MOUNTED_FILESYSTEM__IDENTIFIER"] = "mounted"
    os.environ["LUME_MOUNTED_FILESYSTEM__MOUNT_PATH"] = mount_path
    os.environ["LUME_MOUNTED_FILESYSTEM__MOUNT_ALIAS"] = "/User/my_user/data"
    return MountedFilesystem(
        mount_path=mount_path, mount_alias="/User/my_user/data", identifier="mounted"
    )


## ENVIRONMENT VARIABLES:
# @pytest.fixture(autouse=True)
# def mock_settings_env_vars():
#    with mock.patch.dict(os.environ, {"FROBNICATION_COLOUR": "ROUGE"}):
#        yield
