import click
from lume_services.config import LUMEServicesSettings, get_env_vars
from lume_services.docker.compose import run_docker_services
from lume_services.errors import EnvironmentNotConfiguredError
import time


@click.group()
def docker():
    pass


def wait():
    time.sleep(2)


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
@click.option(
    "--persist",
    default=False,
    help="Persist data between sessions.",
)
def start_services(project_name, timeout, pause, persist: bool):
    """CLI utility for spinning up LUME-services with docker-compose. Services will
    exit on KeyboardInterrupt (Ctrl+C).

    """
    lume_services_settings = LUMEServicesSettings()
    if lume_services_settings.prefect is None:
        env_vars = get_env_vars()
        raise EnvironmentNotConfiguredError(env_vars)

    try:
        with run_docker_services(
            lume_services_settings,
            timeout,
            pause,
            project_name=project_name,
            ui=True,
            persist=persist,
        ):
            print("All services started and passing health checks.")
            while True:
                wait()
    except KeyboardInterrupt:
        print("Shutting down LUME-services.")
