import os

import docker
import pytest
from lume_services.docker.compose import (
    run_docker_services,
)


import logging

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def docker_compose_project_name():
    """Generate a project name using the current process PID. Override this
    fixture in your tests if you need a particular project name."""

    return "pytest{}".format(os.getpid())


@pytest.fixture(scope="session", autouse=True)
def docker_services(
    lume_services_settings,
    docker_compose_project_name,
):
    """Start all services from a docker compose file (`docker-compose up`).
    After test are finished, shutdown all services (`docker-compose down`)."""

    with run_docker_services(
        lume_services_settings,
        timeout=60.0,
        pause=1.0,
        project_name=docker_compose_project_name,
        ui=False,
    ) as docker_service:
        yield docker_service

    logger.info("Stopping docker services.")


@pytest.mark.usefixtures("docker_services")
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
