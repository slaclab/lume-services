import pytest
import os
from lume_services.tests.files.flows import flow1, flow2, flow3
from subprocess import Popen, PIPE, STDOUT
import time

from prefect import Client


@pytest.fixture(scope="session")
def apollo_host_port(request):
    port = request.config.getini("apollo_host_port")
    os.environ["APOLLO_HOST_PORT"] = port
    return port


@pytest.fixture(scope="session")
def hasura_host_port(request):
    port = request.config.getini("hasura_host_port")
    os.environ["HASURA_HOST_PORT"] = port
    return port


@pytest.fixture(scope="session")
def graphql_host_port(request):
    port = request.config.getini("graphql_host_port")
    os.environ["GRAPHQL_HOST_PORT"] = port
    return port


@pytest.fixture(scope="session")
def postgres_db(request):
    db = request.config.getini("postgres_db")
    os.environ["POSTGRES_DB"] = db
    return db


@pytest.fixture(scope="session")
def postgres_user(request):
    user = request.config.getini("postgres_user")
    os.environ["POSTGRES_USER"] = user
    return user


@pytest.fixture(scope="session")
def postgres_password(request):
    password = request.config.getini("postgres_password")
    os.environ["POSTGRES_PASSWORD"] = password
    return password


@pytest.fixture(scope="session")
def postgres_data_path(tmp_path_factory):
    temp_path = tmp_path_factory.mktemp("postgres_data_path")
    os.environ["POSTGRES_DATA_PATH"] = str(temp_path)
    return temp_path


@pytest.fixture(scope="session")
def prefect_api_str(apollo_host_port):
    return f"http://localhost:{apollo_host_port}"


@pytest.fixture(scope="session")
def prefect_tenant(prefect_api_str):

    # Get a client with the correct server port
    client = Client(api_server=prefect_api_str)
    client.graphql("query{hello}", retry_on_api_error=False)
    time.sleep(2)
    client.create_tenant(name="default", slug="default")


@pytest.fixture(scope="session")
def prefect_docker_agent(prefect_tenant, prefect_api_str):

    agent_proc = Popen(
        [
            "prefect",
            "agent",
            "docker",
            "start",
            "--label",
            "lume-services",
            "--network",
            "prefect-server",
            "--no-pull",
            "--api",
            prefect_api_str,
        ],
        stdout=PIPE,
        stderr=STDOUT,
    )
    # Give the agent time to start
    time.sleep(2)

    # Check it started successfully
    assert not agent_proc.poll(), agent_proc.stdout.read().decode("utf-8")
    yield agent_proc
    # Shut it down at the end of the pytest session
    agent_proc.terminate()


@pytest.fixture(scope="session")
def registered_flows(prefect_docker_agent):

    # add module storage
    flow1.register()
    flow2.register()
    flow3.register()
