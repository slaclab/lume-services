import pytest
import os

from subprocess import Popen, PIPE
import time

from prefect import Client
import docker

from lume_services.services.scheduling import (
    PrefectConfig,
    PrefectGraphQLConfig,
    PrefectServerConfig,
)
from lume_services.services.scheduling.backends import (
    DockerBackend,
    DockerHostConfig,
    DockerRunConfig,
)

from lume_services.tests.fixtures.docker import *  # noqa: F403, F401


@pytest.fixture(scope="session", autouse=True)
def prefect_docker_tag():
    return "pytest-prefect"


@pytest.fixture(scope="session")
def prefect_job_docker(rootdir, prefect_docker_tag):
    client = docker.from_env()
    image, _ = client.images.build(
        path=str(rootdir),
        dockerfile=f"{rootdir}/Dockerfile",
        nocache=False,
        tag=prefect_docker_tag,
        quiet=False,
        target="dev",
        rm=True,
        forcerm=True,
    )
    yield image

    client.images.remove(image.id, noprune=False)


@pytest.fixture(scope="session")
def prefect_tenant(prefect_api_str):

    # Get a client with the correct server port
    client = Client(api_server=prefect_api_str)
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
            #  "--label",
            #  "lume-services",
            "--network",
            "prefect-server",
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


@pytest.fixture(scope="session", autouse=True)
def prefect_config(apollo_host_port, graphql_host_port):
    config = PrefectConfig(
        backend=DockerBackend(),
        server=PrefectServerConfig(host_port=apollo_host_port),
        graphql=PrefectGraphQLConfig(host_port=graphql_host_port),
    )
    config.apply()

    return config


@pytest.fixture(scope="session", autouse=True)
def docker_run_config(
    prefect_docker_tag, docker_services, prefect_job_docker, file_service
):
    lume_env = {name: val for name, val in os.environ.items() if "LUME" in name}

    # Need to convert to docker network hostnames
    lume_env["LUME_RESULTS_DB__HOST"] = "mongodb"
    lume_env["LUME_MODEL_DB__HOST"] = "mysql"

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

    host_config = DockerHostConfig(mounts=mounts)

    return DockerRunConfig(
        image=prefect_docker_tag, env=lume_env, host_config=host_config
    )


@pytest.fixture(scope="session", autouse=True)
def docker_backend(prefect_docker_tag, docker_run_config):
    return DockerBackend(default_image=prefect_docker_tag, run_config=docker_run_config)
