import os

import docker
import pytest
from lume_services.docker.compose import (
    get_docker_ip,
    get_setup_command,
    get_cleanup_commands,
    run_docker_services,
)


import logging

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def docker_ip():
    """Determine the IP address for TCP connections to Docker containers."""

    return get_docker_ip()


@pytest.fixture(scope="session")
def docker_compose_project_name():
    """Generate a project name using the current process PID. Override this
    fixture in your tests if you need a particular project name."""

    return "pytest{}".format(os.getpid())


@pytest.fixture(scope="session")
def docker_cleanup():
    """Get the docker_compose command to be executed for test clean-up actions.
    Override this fixture in your tests if you need to change clean-up actions.
    Returning anything that would evaluate to False will skip this command."""

    return get_cleanup_commands()


@pytest.fixture(scope="session")
def docker_setup():
    """Get the docker_compose command to be executed for test setup actions.
    Override this fixture in your tests if you need to change setup actions.
    Returning anything that would evaluate to False will skip this command."""

    return get_setup_command()


@pytest.fixture(scope="session")
def docker_services(
    docker_compose_file,
    lume_services_settings,
    docker_compose_project_name,
):
    """Start all services from a docker compose file (`docker-compose up`).
    After test are finished, shutdown all services (`docker-compose down`)."""

    with run_docker_services(
        docker_compose_file,
        lume_services_settings,
        timeout=60.0,
        pause=1.0,
        project_name=docker_compose_project_name,
        ui=False,
    ) as docker_service:
        yield docker_service


@pytest.fixture(scope="session", autouse=True)
def prefect_job_docker(rootdir, prefect_docker_tag, dockerfile):
    docker_client = docker.from_env()
    image, build_logs = docker_client.images.build(
        path=str(rootdir),
        dockerfile=dockerfile,
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
