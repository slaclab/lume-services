import click
from .modeling import generate_schema_docs


@click.group()
def main():
    pass


main.add_command(generate_schema_docs)
