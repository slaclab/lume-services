import click
from .docker import start_docker_services


@click.group()
def main():
    pass


main.add_command(start_docker_services)

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
