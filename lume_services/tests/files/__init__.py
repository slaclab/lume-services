from pkg_resources import resource_filename

PYTEST_DOCKER_COMPOSE = resource_filename(
    "lume_services.tests.files", "docker-compose.yml"
)

SAMPLE_TEXT_FILE = resource_filename("lume_services.tests.files", "sample_text.txt")

SAMPLE_IMAGE_FILE = resource_filename("lume_services.tests.files", "sample_image.png")

SAMPLE_YAML_FILE = resource_filename("lume_services.tests.files", "sample_yaml.yml")

SAMPLE_IMPACT_ARCHIVE = resource_filename(
    "lume_services.tests.files", "sample_impact_archive.h5"
)
