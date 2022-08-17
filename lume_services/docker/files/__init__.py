from pkg_resources import resource_filename

DOCKER_COMPOSE = resource_filename("lume_services.docker.files", "docker-compose.yml")
MODEL_DB_INIT = resource_filename("lume_services.docker.files", "model-db-init.sql")
