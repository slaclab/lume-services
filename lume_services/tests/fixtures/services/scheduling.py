import pytest
import os

from subprocess import Popen, PIPE
import time

from prefect import Client

from lume_services.services.scheduling import (
    PrefectConfig,
    PrefectGraphQLConfig,
    PrefectServerConfig,
)
from lume_services.services.scheduling.backends import (
    DockerBackend,
    DockerRunConfig,
    DockerHostConfig,
)

from lume_services.tests.fixtures.docker import *  # noqa: F403, F401


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
def docker_run_config(prefect_job_docker, docker_services):
    lume_env = {name: val for name, val in os.environ.items() if "LUME" in name}

    # Need to convert to docker network hostnames
    lume_env["LUME_RESULTS_DB__HOST"] = "mongodb"
    lume_env["LUME_MODEL_DB__HOST"] = "mysql"

    return DockerRunConfig(
        image=prefect_job_docker, env=lume_env, host_config=DockerHostConfig()
    )


@pytest.fixture(scope="session", autouse=True)
def docker_backend(prefect_job_docker, docker_run_config):
    return DockerBackend(default_image=prefect_job_docker, run_config=docker_run_config)


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
