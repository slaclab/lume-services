import click
from .modeling.schema import generate_schema_docs

@click.group()
def main():
    pass

main.add_command(generate_schema_docs)
