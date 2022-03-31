from typing import List
from pydantic import BaseSettings

from contextlib import contextmanager

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine.base import Connection
from sqlalchemy.orm import sessionmaker, scoped_session
import os

from lume_services.database.model.db import ModelDB, ModelDBConfig

from pkg_resources import resource_filename
from contextvars import ContextVar
from contextlib import contextmanager


MYSQL_MODEL_SCHEMA = resource_filename(".", "schema.sql")
# guesses: r.successful, r.dict


"""
class ModelDBConfig(BaseSettings):
    db_uri_template: str = "mysql+pymysql://${user}:${password}@${host}:${port}/${database}"
    pool_size: int
    password: str
    user: str
    host: str
    port: int
    database: str
"""

class MySQLConfig(BaseSettings):
    db_uri: str
    pool_size: int


class MySQLConnHandler(BaseSettings):

    def __init__(self, *, config: MySQLConfig):
        self.config = config


    def _create_engine(self):
        self.pid = os.getpid()

        # can possible pass args here...
        connect_args = {}

        # since using a context manager, must have context-local managed vars
        self._connection = ContextVar("connection", default=None)

        # pool_pre_ping provides liveliness check
        self.engine=create_engine(self.config.db_uri, connect_args, pool_pre_ping=True, pool_size=self.config.pool_size)

        # don't really need now
        # create a scoped session
        # self.orm_sessionmaker = sessionmaker(bind=self.engine)
        #self.session = scoped_session(self.orm_sessionmaker)

    def _connect(self) -> Connection:
        connection = self.engine.connect()
        self._connection.set(connection)
        return connection

    def _check_mp(self):

        # check pid against object pid and create new engine in event of another process
        if os.getpid() != self.pid:
            self._create_engine()
    

    def _connect(self) -> Connection:
        self._connection = self._engine.connect()
        # update inspector
        self._inspector = inspect(self._engine)
        return self._connection


    @property
    def _currect_connection(self) -> Connection:
        return self._connection.get()


    @contextmanager
    def connection(self) -> Connection:
        """This is a context manager bc we want to be able to release connection when finished
        """
        # Add cleanup on exit check

        self._check_mp()

        # get connection
        connection = self._connection.get()
        if connection is None:
            self._connect()

        try:
            yield connection

        finally:
            connection = self._connection.get()

            if connection:
                self._connection.close()


    def execute(self, sql, *args, **kwargs):
        with self.connection() as conn:
            
            r = conn.execute(sql, *args, **kwargs)

        return r



class MySQLModelDB(ModelDB):
    """
    Not safe with mutiprocessing at present
    
    """
    def __init__(self, *, db_config: ModelDBConfig, db_conn_handler: MySQLConnHandler):

        super().__init__()

        self._config = db_config
        self._connection = None
        self._create_engine()
        self._conn_handler = 


    
    def execute(self, sql, *args, **kwargs):
        self._
        
        with self.connection() as conn:
            
            r = conn.execute(sql, *args, **kwargs)

        return r

    