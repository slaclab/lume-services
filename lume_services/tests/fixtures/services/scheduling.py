import pytest
import os

import prefect

import docker

from lume_services.services.scheduling.backends.server import (
    PrefectConfig,
    PrefectGraphQLConfig,
    PrefectHasuraConfig,
    PrefectPostgresConfig,
    PrefectServerConfig,
)
from lume_services.services.scheduling.backends import (
    DockerBackend,
    DockerRunConfig,
)
from lume_services.services.scheduling.service import SchedulingService

import logging

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def prefect_docker_tag():
    return "lume_services:pytest"
    # return "build-test:latest"


@pytest.fixture(scope="session", autouse=True)
def prefect_config(
    server_host,
    server_host_port,
    graphql_host,
    graphql_host_port,
    hasura_host,
    hasura_host_port,
    postgres_host,
    postgres_host_port,
    postgres_db,
    postgres_user,
    postgres_password,
    postgres_data_path,
):
    config = PrefectConfig(
        backend="server",
        server=PrefectServerConfig(host=server_host, host_port=server_host_port),
        graphql=PrefectGraphQLConfig(host=graphql_host, host_port=graphql_host_port),
        hasura=PrefectHasuraConfig(host=hasura_host, host_port=hasura_host_port),
        postgres=PrefectPostgresConfig(
            host=postgres_host,
            host_port=postgres_host_port,
            db=postgres_db,
            user=postgres_user,
            password=postgres_password,
            data_path=postgres_data_path,
        ),
    )

    return config


@pytest.fixture(scope="session", autouse=True)
def prefect_job_docker(rootdir, prefect_docker_tag):
    docker_client = docker.from_env()
    image, build_logs = docker_client.images.build(
        path=str(rootdir),
        dockerfile=f"{rootdir}/Dockerfile",
        nocache=True,
        tag=prefect_docker_tag,
        quiet=False,
        buildargs={"LUME_SERVICES_VERSION": "pytest"},
        rm=True,
        forcerm=True,
    )
    for chunk in build_logs:
        if "stream" in chunk:
            for line in chunk["stream"].splitlines():
                logger.info(line)

    yield image

    docker_client.images.remove(image.id, noprune=False)


def is_prefect_ready(prefect_api_str):
    try:
        client = prefect.Client(api_server=prefect_api_str)
        client.graphql("query{hello}", retry_on_api_error=False)
        return True
    except Exception as e:
        logger.error(e)
        return False


# allows us to wait until we get a response from the Prefect services
# and allow startup time
@pytest.fixture(scope="session", autouse=True)
def prefect_services(docker_services, prefect_api_str):
    docker_services.wait_until_responsive(
        timeout=60.0,
        pause=1,
        check=lambda: is_prefect_ready(prefect_api_str),
    )
    return


@pytest.mark.usefixtures("prefect_config")
@pytest.mark.usefixtures("prefect_services")
@pytest.fixture(scope="session", autouse=True)
def prefect_client(prefect_api_str):
    client = prefect.Client(api_server=prefect_api_str)
    return client


@pytest.fixture(scope="session", autouse=True)
def lume_env():
    lume_env = {name: val for name, val in os.environ.items() if "LUME" in name}
    # Need to convert to docker network hostnames
    lume_env["LUME_RESULTS_DB__HOST"] = "mongodb"
    lume_env["LUME_MODEL_DB__HOST"] = "mysql"
    return lume_env


@pytest.mark.usefixtures("prefect_services")
@pytest.fixture(scope="session", autouse=True)
def docker_run_config(prefect_docker_tag, file_service, lume_env):

    mounted_filesystems = file_service.get_mounted_filesystems()
    mounts = []
    for filesystem in mounted_filesystems.values():
        mounts.append(
            {
                "target": filesystem.mount_alias,
                "source": filesystem.mount_path,
                "type": "bind",
            }
        )

    host_config = {"mounts": mounts}

    return DockerRunConfig(
        image=prefect_docker_tag, env=lume_env, host_config=host_config
    )


@pytest.mark.usefixtures("prefect_services")
@pytest.fixture(scope="session", autouse=True)
def docker_backend(prefect_config):
    os.environ["LUME_BACKEND"] = "docker"
    return DockerBackend(config=prefect_config)


@pytest.mark.usefixtures("prefect_services")
@pytest.mark.usefixtures("docker_backend")
@pytest.fixture(scope="session", autouse=True)
def scheduling_service(docker_backend):
    return SchedulingService(backend=docker_backend)
