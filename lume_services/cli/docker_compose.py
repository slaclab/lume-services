import click
from lume_services.config import LUMEServicesSettings
from lume_services.docker.compose import run_docker_services
import time


@click.group()
def docker():
    pass


@docker.command(help="Start cluster of docker services.")
@click.option(
    "--project_name",
    default="lume-services",
    help="Name of docker project for labeling docker-compose.",
)
@click.option(
    "--timeout",
    default=60.0,
    help="Time allotted for successful docker-compose startup.",
)
@click.option(
    "--pause",
    default=1.0,
    help="Pause between successive polls of docker-compose services.",
)
def start_services(project_name, timeout, pause):
    """CLI utility for spinning up LUME-services with docker-compose. Services will
    exit on KeyboardInterrupt (Ctrl+C).

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
