from {{ cookiecutter.project_slug }}.flow.flow import get_flow
import click


@click.command()
@click.argument('filename')
def main(filename):
    flow = get_flow()

    if not filename[-4:] == ".png":
        filename = filename + ".png"

    flow.visualize(filename, format="png")
