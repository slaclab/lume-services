import click
from .docker_compose import docker
from lume_services.config import configure


@click.group()
@click.pass_context
def main(ctx):
    # configure lume services
    configure()


main.add_command(docker)


"""
import click

CONTEXT_SETTINGS = dict(
    default_map={'runserver': {'port': 5000}}
)

@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    pass

@cli.command()
@click.option('--port', default=8000)
def runserver(port):
    click.echo(f"Serving on http://127.0.0.1:{port}/")

if __name__ == '__main__':
    cli()
"""
