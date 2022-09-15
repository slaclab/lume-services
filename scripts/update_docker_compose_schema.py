from lume_services.services.models.db.schema import Base
from lume_services.docker.files import MODEL_DB_INIT
from sqlalchemy import create_mock_engine, create_engine, insert
from sqlalchemy import insert
import click


def build_db_schema() -> str:
    """Utility function for creating db init for docker-compose."""

    buffer = []

    def executor(sql, *a, **kw):
        stmt = sql.compile(dialect=engine.dialect)
        buffer.append(stmt)

    engine = create_mock_engine("mysql://", executor)

    Base.metadata.create_all(engine)

    return [str(buf) for buf in buffer]


@click.command()
@click.option("--filename", required=False, type=str, default=str(MODEL_DB_INIT))
def build_docker_compose_schema(filename: str):

    commands = build_db_schema()

    with open(filename, "w") as f:
        for command in commands:

            command = command[:-2]  # drop newline at end
            f.write(command + ";")

        f.write("\n")


@click.group()
def main():
    pass


main.add_command(build_docker_compose_schema)


if __name__ == "__main__":
    main()
