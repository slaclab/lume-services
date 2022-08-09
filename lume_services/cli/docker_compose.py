import click
from lume_services.config import LUMEServicesSettings
from lume_services.docker.compose import run_docker_services
import time


@click.group()
def docker():
    pass


@docker.command()
@click.option("--project_name", default="lume-services")
@click.option("--timeout", default=60.0)
@click.option("--pause", default=1.0)
def start_docker_services(project_name, timeout, pause):
    """CLI utility for spinning up LUME-services with docker-compose. Services will
    exit on KeyboardInterrupt (Ctrl+C).

    Args:
        project_name
        timeout
        pause

    """
    lume_services_settings = LUMEServicesSettings()
    try:
        with run_docker_services(
            lume_services_settings, timeout, pause, project_name=project_name, ui=True
        ):
            print("All services started and passing health checks.")
            while True:
                time.sleep(2)
    except KeyboardInterrupt:
        print("Shutting down LUME-services ")


if __name__ == "__main__":
    docker()
