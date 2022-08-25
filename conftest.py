import pytest
import os
import logging

from lume_services import config
from lume_services.docker.files import DOCKER_COMPOSE
from lume_services.services.models.db import ModelDBConfig
from lume_services.services.results.mongodb import MongodbResultsDBConfig
from lume_services.services.scheduling.backends.server import (
    PrefectAgentConfig,
    PrefectConfig,
    PrefectServerConfig,
)

from lume_services.services.files.filesystems import (
    LocalFilesystem,
    MountedFilesystem,
)


def pytest_addoption(parser):
    parser.addini("backend", default="docker", help="Backend interface to use")
    parser.addini(
        "prefect_backend", default="server", help="Prefect backend: server or cloud"
    )
    parser.addini("mysql_host", default="127.0.0.1", help="MySQL host")
    parser.addini("mysql_port", default=3306, help="MySQL port")
    parser.addini("mysql_user", default="root", help="MySQL user")
    parser.addini("mysql_password", default="root", help="MySQL password")
    parser.addini("mysql_database", default="model_db", help="Model database name")
    parser.addini("mysql_poolsize", default=1, help="MySQL client poolsize")

    parser.addini("mongodb_host", default="127.0.0.1", help="MySQL host")
    parser.addini("mongodb_port", default=27017, help="MySQL port")
    parser.addini("mongodb_user", default="root", help="MySQL user")
    parser.addini("mongodb_password", default="password", help="MySQL password")
    parser.addini(name="mongodb_database", help="Mysql database name", default="test")

    # prefect
    parser.addini(name="server_tag", help="Prefect server image tag", default="latest")
    parser.addini(
        name="server_host_port", help="Prefect server apollo api port", default=4200
    )
    parser.addini(
        name="server_host", help="Prefect server apollo host IP", default="127.0.0.1"
    )
    parser.addini(name="agent_host", help="Prefect agent host", default="127.0.0.1")
    parser.addini(
        name="agent_host_port", help="Prefect agent port for comms", default=5000
    )


@pytest.fixture(scope="session", autouse=True)
def rootdir(request):
    rootdir = request.config.rootpath
    os.environ["LUME_SERVICES_ROOTDIR"] = str(rootdir)
    return rootdir


@pytest.fixture(scope="session", autouse=True)
def lume_backend(request):
    lume_backend = request.config.getini("backend")
    os.environ["LUME_BACKEND"] = lume_backend
    return lume_backend


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


@pytest.fixture(scope="session")
def server_tag(request):
    tag = request.config.getini("server_tag")
    os.environ["LUME_PREFECT__SERVER__TAG"] = tag
    return tag


@pytest.fixture(scope="session")
def prefect_backend(request):
    backend = request.config.getini("prefect_backend")
    os.environ["LUME_PREFECT__SERVER__BACKEND"] = backend
    return backend


@pytest.fixture(scope="session")
def server_host_port(request):
    port = request.config.getini("server_host_port")
    os.environ["LUME_PREFECT__SERVER__HOST_PORT"] = port
    return port


@pytest.fixture(scope="session")
def server_host(request):
    port = request.config.getini("server_host")
    os.environ["LUME_PREFECT__SERVER__HOST"] = port
    return port


@pytest.fixture(scope="session")
def agent_host(request):
    host = request.config.getini("agent_host")
    os.environ["LUME_PREFECT__AGENT__HOST"] = host
    return host


@pytest.fixture(scope="session")
def agent_host_port(request):
    port = request.config.getini("agent_host_port")
    os.environ["LUME_PREFECT__AGENT__HOST_PORT"] = port
    return port


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


# Scheduling

# Filesystem
@pytest.fixture(scope="session")
def mount_path(tmp_path_factory):
    return str(tmp_path_factory.mktemp("mounted_dir"))


@pytest.fixture(scope="session", autouse=True)
def local_filesystem():
    return LocalFilesystem()


@pytest.fixture(scope="session", autouse=True)
def mounted_filesystem(mount_path):
    os.environ["LUME_MOUNTED_FILESYSTEM__IDENTIFIER"] = "mounted"
    os.environ["LUME_MOUNTED_FILESYSTEM__MOUNT_PATH"] = mount_path
    os.environ["LUME_MOUNTED_FILESYSTEM__MOUNT_ALIAS"] = "/User/my_user/data"
    return MountedFilesystem(
        mount_path=mount_path, mount_alias="/User/my_user/data", identifier="mounted"
    )


# Docker


@pytest.fixture(scope="session", autouse=True)
def prefect_docker_tag():
    return "lume_services:pytest"


@pytest.fixture(scope="session", autouse=True)
def dockerfile(rootdir):
    return f"{rootdir}/Dockerfile"


## ENVIRONMENT VARIABLES:
# @pytest.fixture(autouse=True)
# def mock_settings_env_vars():
#    with mock.patch.dict(os.environ, {"FROBNICATION_COLOUR": "ROUGE"}):
#        yield

# Full configuration


@pytest.fixture(scope="session", autouse=True)
def lume_services_settings(
    mysql_host,
    mysql_port,
    mysql_user,
    mysql_password,
    mysql_database,
    mongodb_host,
    mongodb_port,
    mongodb_user,
    mongodb_password,
    mongodb_database,
    server_host_port,
    server_host,
    server_tag,
    agent_host,
    agent_host_port,
    prefect_backend,
    lume_backend,
    mounted_filesystem,
):
    model_db_config = ModelDBConfig(
        host=mysql_host,
        port=mysql_port,
        user=mysql_user,
        password=mysql_password,
        database=mysql_database,
    )

    results_db_config = MongodbResultsDBConfig(
        port=mongodb_port,
        host=mongodb_host,
        username=mongodb_user,
        database=mongodb_database,
        password=mongodb_password,
    )

    prefect_config = PrefectConfig(
        server=PrefectServerConfig(
            host=server_host, host_port=server_host_port, tag=server_tag
        ),
        agent=PrefectAgentConfig(host=agent_host, host_port=agent_host_port),
        backend=prefect_backend,
    )

    settings = config.LUMEServicesSettings(
        model_db=model_db_config,
        results_db=results_db_config,
        prefect=prefect_config,
        backend=lume_backend,
        mounted_filesystem=mounted_filesystem,
    )

    return settings


# Now setup all fixtures
pytest_plugins = [
    "lume_services.tests.fixtures.docker",
    "lume_services.tests.fixtures.services.files",
    "lume_services.tests.fixtures.services.models",
    "lume_services.tests.fixtures.services.results",
    "lume_services.tests.fixtures.services.scheduling",
]
