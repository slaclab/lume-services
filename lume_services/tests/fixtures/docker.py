import contextlib
import os

import pytest
from lume_services.docker.files import DOCKER_COMPOSE
from lume_services.docker.compose import (
    Services,
    get_docker_ip,
    DockerComposeExecutor,
    get_setup_command,
    get_cleanup_commands,
)


@pytest.fixture(scope="session", autouse=True)
def docker_config(
    mysql_host,
    mysql_user,
    mysql_port,
    mysql_password,
    server_host,
    server_host_port,
    hasura_host_port,
    hasura_host,
    graphql_host,
    graphql_host_port,
    postgres_db,
    postgres_user,
    postgres_password,
    postgres_data_path,
    mongodb_host,
    mongodb_user,
    mongodb_port,
    mongodb_database,
    mongodb_password,
    mounted_filesystem,
):
    pass


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


@contextlib.contextmanager
def get_docker_services(
    docker_compose_file,
    docker_compose_project_name,
    docker_setup,
    docker_cleanup,
    docker_config,
):
    docker_compose = DockerComposeExecutor(
        docker_compose_file, docker_compose_project_name
    )

    # setup containers.
    if docker_setup:
        docker_compose.execute(docker_setup)

    try:
        # Let test(s) run.
        yield Services(docker_compose)
    finally:
        # Clean up.
        if docker_cleanup is not None:
            for cmd in docker_cleanup:
                docker_compose.execute(cmd)


@pytest.fixture(scope="session")
def docker_services(
    docker_compose_file,
    docker_compose_project_name,
    docker_setup,
    docker_cleanup,
    docker_config,
):
    """Start all services from a docker compose file (`docker-compose up`).
    After test are finished, shutdown all services (`docker-compose down`)."""

    with get_docker_services(
        docker_compose_file,
        docker_compose_project_name,
        docker_setup,
        docker_cleanup,
        docker_config,
    ) as docker_service:
        yield docker_service


@pytest.fixture(scope="session")
def docker_compose_file():
    return DOCKER_COMPOSE
