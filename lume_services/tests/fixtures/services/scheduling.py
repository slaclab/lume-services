import pytest
import os

from subprocess import Popen, PIPE
import time
import prefect

import docker

from lume_services.services.scheduling.backends.server import (
    PrefectConfig,
    PrefectGraphQLConfig,
    PrefectHasuraConfig,
    PrefectServerConfig,
)
from lume_services.services.scheduling.backends import (
    DockerBackend,
    DockerRunConfig,
)

from lume_services.tests.fixtures.docker import *  # noqa: F403, F401
from lume_services.tests.fixtures.services.files import *  # noqa: F403, F401

import logging

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def prefect_docker_tag():
    return "lume_services:pytest"
    # return "build-test:latest"


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
def prefect_tenant(prefect_api_str):

    # Get a client with the correct server port
    client = prefect.Client(api_server=prefect_api_str)
    client.graphql("query{hello}", retry_on_api_error=False)
    time.sleep(2)
    client.create_tenant(name="default", slug="default")


@pytest.fixture(scope="session")
def prefect_docker_agent(prefect_tenant, prefect_api_str):

    agent_proc = Popen(
        [
            "prefect",
            "agent",
            "docker",
            "start",
            "--label",
            "lume-services",
            "--network",
            "prefect-server",
            "--show-flow-logs",
            "--no-pull",
            "--api",
            prefect_api_str,
        ],
        stdout=PIPE,
        stderr=PIPE,
    )
    # Give the agent time to start
    time.sleep(2)

    # Check it started successfully
    assert not agent_proc.poll(), agent_proc.stdout.read().decode("utf-8")
    yield agent_proc
    # Shut it down at the end of the pytest session
    agent_proc.terminate()

    output = agent_proc.communicate()[0]
    for line in output.split(b"\n"):
        logger.debug(output)


@pytest.fixture(scope="session", autouse=True)
def prefect_config(server_host_port, graphql_host_port, hasura_host_port):
    config = PrefectConfig(
        server=PrefectServerConfig(host_port=server_host_port),
        graphql=PrefectGraphQLConfig(host_port=graphql_host_port),
        hasura=PrefectHasuraConfig(host_port=hasura_host_port),
    )
    config.apply()

    return config


@pytest.fixture(scope="session", autouse=True)
def lume_env():
    lume_env = {name: val for name, val in os.environ.items() if "LUME" in name}
    # Need to convert to docker network hostnames
    lume_env["LUME_RESULTS_DB__HOST"] = "mongodb"
    lume_env["LUME_MODEL_DB__HOST"] = "mysql"
    return lume_env


@pytest.fixture(scope="session", autouse=True)
def docker_run_config(
    prefect_docker_tag, docker_services, prefect_job_docker, file_service, lume_env
):

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


@pytest.fixture(scope="session", autouse=True)
def docker_backend(prefect_config):
    return DockerBackend(config=prefect_config)


@pytest.fixture(scope="session", autouse=True)
def prefect_client(prefect_api_str, prefect_docker_agent):
    client = prefect.Client(api_server=prefect_api_str)
    client.graphql("query{hello}", retry_on_api_error=False)
    return client
