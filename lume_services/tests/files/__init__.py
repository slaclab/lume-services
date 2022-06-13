from pkg_resources import resource_filename

PYTEST_DOCKER_COMPOSE = resource_filename(
    "lume_services.tests.files", "docker-compose.yml"
)
