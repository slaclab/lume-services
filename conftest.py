from multiprocessing import pool
import pytest 
from pytest_mysql import factories
from sqlalchemy.engine.base import Connection
from sqlalchemy import create_engine
from string import Template



from lume_services.database.model.mysql import MYSQL_MODEL_SCHEMA, MySQLConfig, MySQLService
from lume_services.database.model.db import DBService, DBServiceConfig, DBServiceConfig, DBSchema, ModelDBService

class MockDBServiceConfig(DBServiceConfig):
    """Assigning connection directly
    
    """
    mysql_cxn: Connection


class MockMySQLService(DBService):

    def __init__(self, db_config: MockDBServiceConfig):
        self.connection = db_config.mysql_cxn

    def execute(self, sql, *args, **kwargs):
        with self.connection() as cxn:
            
            r = cxn.execute(sql, *args, **kwargs)

        return r

mysql_server = factories.mysql_proc()


"""
@pytest.mark.skip
@pytest.fixture
def model_db_schema():
    return DBSchema(
    model_table="models",
    deployment_table="deployments",
    flow_table="flows",
    project_table="projects",
    flow_to_deployments_table="flow_to_deployments",
    )


@pytest.mark.skip
@pytest.fixture(scope="module", autouse=True)
def model_db_service(mysql, model_db_schema):
    
    db_service_config = MockDBServiceConfig(
        mysql_cxn = mysql,
        schema = model_db_schema
    )
    db_service = MockMySQLService(db_service_config)

    model_db_service = ModelDBService(db_service)

    return model_db_service
"""

def pytest_addoption(parser):

    parser.addini(
        "mysql_user", default="root", help="MySQL user"
    )

    parser.addini(
        "mysql_database", default="model_db", help="Model database name"
    )

    parser.addini(
        "mysql_poolsize", default=1, help="MySQL client poolsize"
    )


@pytest.fixture(scope="session", autouse=True)
def mysql_user(request):
    return request.config.getini("mysql_user")

@pytest.fixture(scope="session", autouse=True)
def mysql_host(request):
    return request.config.getini("mysql_host")


@pytest.fixture(scope="session", autouse=True)
def mysql_port(request):
    return int(request.config.getini("mysql_port"))


@pytest.fixture(scope="session", autouse=True)
def mysql_database(request):
    return request.config.getini("mysql_database")


@pytest.fixture(scope="session", autouse=True)
def mysql_pool_size(request):
    return int(request.config.getini("mysql_poolsize"))


@pytest.fixture(scope="session", autouse=True)
def mysql_schema_cmds():
    file = open(MYSQL_MODEL_SCHEMA, 'r')
    sql = ''
    line = file.readline()
    while line:
        sql += ' ' + line.strip('\n').strip('\t')
        line = file.readline()

    cmds = sql.split(";")
    return [f"{cmd};" for cmd in cmds[:-1] ]

@pytest.fixture(scope="session", autouse=True)
def model_db_schema_config():
    return DBSchema(
        model_table="models",
        deployment_table="deployments",
        flow_table="flows",
        project_table="projects",
        flow_to_deployments_table="flow_to_deployments",
    )


@pytest.fixture(scope="session", autouse=True)
def base_db_uri(mysql_user, mysql_host, mysql_port):
    return Template("mysql+pymysql://${user}:@${host}:${port}").substitute(user=mysql_user, host=mysql_host, port=mysql_port)


@pytest.fixture(scope="session", autouse=True)
def mysql_config(mysql_user, mysql_host, mysql_port, mysql_database, mysql_pool_size, model_db_schema_config):

    db_uri = Template("mysql+pymysql://${user}:@${host}:${port}/${database}").substitute(user=mysql_user, host=mysql_host, port=mysql_port, database=mysql_database)

    return MySQLConfig(
        db_uri=db_uri,
        pool_size=mysql_pool_size,
        db_schema=model_db_schema_config,
    )


@pytest.mark.usefixtures("mysql_proc")
@pytest.fixture(scope="module", autouse=True)
def mysql_service(mysql_config):
    mysql_service = MySQLService(mysql_config)
    return mysql_service



@pytest.mark.usefixtures("mysql_proc")
@pytest.fixture(scope="module", autouse=True)
def model_db_service(mysql_service, mysql_database, mysql_schema_cmds, base_db_uri, mysql_proc):

    # start the mysql process if not started
    if not mysql_proc.running():
        mysql_proc.start()

    import time
    #time.sleep(10000)

    engine = create_engine(base_db_uri, pool_size=1)
    with engine.connect() as connection:
        for cmd in mysql_schema_cmds:
            print(cmd)
            result = connection.execute(cmd)

    model_db_service = ModelDBService(mysql_service)

    # set up database
    yield model_db_service

    sql = f"""
    DROP DATABASE {mysql_database};
    
    """

    model_db_service._db_service.execute(sql)
    print(base_db_uri)
    print("Teardown")


"""

@pytest.fixture(scope="session", autouse=True)
def mongodb_results_db():
    ...

"""