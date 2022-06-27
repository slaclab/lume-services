from lume_services.services.data.models.db.schema import (
    generate_schema_graph,
    generate_uml_graph,
)
import click


@click.command()
@click.option("--uml_output_filename", required=True, type=str)
@click.option("--schema_output_filename", required=True, type=str)
def generate_schema_docs(schema_output_filename, uml_output_filename):

    generate_schema_graph(schema_output_filename)
    generate_uml_graph(uml_output_filename)
