from sqlalchemy_schemadisplay import create_schema_graph, create_uml_graph
from lume_services.services.models.db.schema import (
    Base,
    Model,
    Deployment,
    Flow,
    Project,
    FlowOfFlows,
)
from sqlalchemy.orm import class_mapper

import click


def generate_schema_graph(
    output_filename: str,
    show_datatypes: bool = True,
    show_indexes: bool = True,
    rankdir: str = "LR",
    concentrate: bool = False,
) -> None:
    """Utility function for creating a png of the schema graph for the schema defined
    in this module.

    Args:
        output_filename (str): Filename of saved output
        show_datatypes (bool): Whether to list datatypes on the graph
        show_indexes (bool): Whether to show indices on the graph
        rankdir (str): Either "LR" left-to-right, or "TB" top-to-bottom organization
        concentrate (bool): Whether to join relation lines together

    """
    # Generate graph of connected database
    graph = create_schema_graph(
        metadata=Base.metadata,
        show_datatypes=show_datatypes,
        show_indexes=show_indexes,
        rankdir=rankdir,
        concentrate=concentrate,
    )

    # Generate png image
    graph.write_png(output_filename)


def generate_uml_graph(output_filename: str):
    """Utility function for creating a png of the uml graph for the schema defined in
    this module.

    Args:
        output_filename (str): Filename of saved output

    """

    # compile mappers
    mappers = [class_mapper(x) for x in [Model, Deployment, Flow, Project, FlowOfFlows]]
    graph = create_uml_graph(
        mappers, show_operations=False, show_multiplicity_one=False
    )

    # generate png image
    graph.write_png(output_filename)


@click.command()
@click.option("--uml_output_filename", required=True, type=str)
@click.option("--schema_output_filename", required=True, type=str)
def generate_schema_docs(schema_output_filename, uml_output_filename):

    generate_schema_graph(schema_output_filename)
    generate_uml_graph(uml_output_filename)


@click.group()
def main():
    pass


main.add_command(generate_schema_docs)


if __name__ == "__main__":
    main()
