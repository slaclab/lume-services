import pytest
import os


@pytest.fixture(scope="session", autouse=True)
def mysql_host(request):
    host = request.config.getini("mysql_host")
    os.environ["MYSQL_HOST"] = host
    return host


@pytest.fixture(scope="session", autouse=True)
def mysql_user(request):
    user = request.config.getini("mysql_user")
    os.environ["MYSQL_USER"] = user
    return user


@pytest.fixture(scope="session", autouse=True)
def mysql_password(request):
    password = request.config.getini("mysql_password")
    os.environ["MYSQL_PASSWORD"] = password
    return password


@pytest.fixture(scope="session", autouse=True)
def mysql_port(request):
    port = request.config.getini("mysql_port")
    os.environ["MYSQL_HOST_PORT"] = port
    return int(port)


@pytest.fixture(scope="session", autouse=True)
def mysql_database(request):
    return request.config.getini("mysql_database")


@pytest.fixture(scope="session", autouse=True)
def mysql_pool_size(request):
    return int(request.config.getini("mysql_poolsize"))


@pytest.fixture(scope="session", autouse=True)
def base_mysql_uri(mysql_user, mysql_password, mysql_host, mysql_port):
    return f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}"


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
def graphql_api_str(apollo_host_port):
    return f"http://localhost:{apollo_host_port}/graphql"


@pytest.fixture(scope="session", autouse=True)
def mongodb_host(request):
    return request.config.getini("mongodb_host")


@pytest.fixture(scope="session", autouse=True)
def mongodb_port(request):
    port = request.config.getini("mongodb_port")
    return int(port)


@pytest.fixture(scope="session", autouse=True)
def mongodb_database(request):
    return request.config.getini("mongodb_dbname")
