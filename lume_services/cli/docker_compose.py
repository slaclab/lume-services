import click
from lume_services.docker.compose import run_docker_services
import time


@click.group()
def docker():
    pass


@docker.command()
@click.option("--project_name", default="lume-services")
def start_docker_services(project_name):
    try:
        with run_docker_services(project_name=project_name, ui=True):
            while True:
                time.sleep(2)
                print("Services started")
    except KeyboardInterrupt:
        print("Shutting down")


if __name__ == "__main__":
    docker()
