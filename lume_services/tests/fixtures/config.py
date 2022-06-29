import pytest


@pytest.fixture(scope="session", autouse=True)
def docker_config(
    mysql_host,
    mysql_user,
    mysql_port,
    mysql_password,
    apollo_host_port,
    hasura_host_port,
    graphql_host_port,
    postgres_db,
    postgres_user,
    postgres_password,
    postgres_data_path,
):
    pass
