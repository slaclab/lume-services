import pytest
import os


@pytest.fixture(scope="session", autouse=True)
def mysql_host(request):
    host = request.config.getini("mysql_host")
    os.environ["MYSQL_HOST"] = host
    os.environ["LUME_MODEL_DB__HOST"] = host
    return host


@pytest.fixture(scope="session", autouse=True)
def mysql_user(request):
    user = request.config.getini("mysql_user")
    os.environ["MYSQL_USER"] = user
    os.environ["LUME_MODEL_DB__USER"] = user
    return user


@pytest.fixture(scope="session", autouse=True)
def mysql_password(request):
    password = request.config.getini("mysql_password")
    os.environ["MYSQL_PASSWORD"] = password
    os.environ["LUME_MODEL_DB__PASSWORD"] = password
    return password


@pytest.fixture(scope="session", autouse=True)
def mysql_port(request):
    port = request.config.getini("mysql_port")
    os.environ["MYSQL_HOST_PORT"] = port
    os.environ["LUME_MODEL_DB__PORT"] = port
    return int(port)


@pytest.fixture(scope="session", autouse=True)
def mysql_database(request):
    database = request.config.getini("mysql_database")
    os.environ["LUME_MODEL_DB__DATABASE"] = database
    return database


@pytest.fixture(scope="session", autouse=True)
def mysql_pool_size(request):
    pool_size = request.config.getini("mysql_poolsize")
    os.environ["LUME_MODEL_DB__POOL_SIZE"] = pool_size
    return int(pool_size)


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
    mongodb_host = request.config.getini("mongodb_host")
    os.environ["LUME_RESULTS_DB__HOST"] = mongodb_host
    return mongodb_host


@pytest.fixture(scope="session", autouse=True)
def mongodb_port(request):
    mongodb_port = request.config.getini("mongodb_port")
    os.environ["LUME_RESULTS_DB__PORT"] = mongodb_port
    return int(mongodb_port)


@pytest.fixture(scope="session", autouse=True)
def mongodb_user(request):
    mongodb_user = request.config.getini("mongodb_user")
    os.environ["LUME_RESULTS_DB__USER"] = mongodb_user
    return mongodb_user


@pytest.fixture(scope="session", autouse=True)
def mongodb_password(request):
    mongodb_password = request.config.getini("mongodb_password")
    os.environ["LUME_RESULTS_DB__PASSWORD"] = mongodb_password
    return mongodb_password


@pytest.fixture(scope="session", autouse=True)
def mongodb_database(request):
    database = request.config.getini("mongodb_dbname")
    os.environ["LUME_RESULTS_DB__DATABASE"] = database
    return database
