from pydantic import BaseSettings

from contextlib import contextmanager

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine.base import Connection
import os

from lume_services.database.model.db import DBServiceConfig, DBConnConfig, DBService

from pkg_resources import resource_filename
from contextvars import ContextVar
from contextlib import contextmanager


MYSQL_MODEL_SCHEMA = resource_filename(".", "schema.sql")
# guesses: r.successful, r.dict


class MySQLConfig(DBConnConfig):
    db_uri: str
    pool_size: int


class MySQLCxnManager(BaseSettings):

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
        cxn = self.engine.connect()
        self._connection.set(cxn)
        return cxn

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
        cxn = self._connection.get()
        if cxn is None:
            self._connect()

        try:
            yield cxn

        finally:
            cxn = self._connection.get()

            if cxn:
                self._connection.close()


    def execute(self, sql, *args, **kwargs):
        with self.connection() as cxn:
            
            r = cxn.execute(sql, *args, **kwargs)

        return r


class MySQService(DBService):

    def __init__(self, *, db_config: DBServiceConfig):

        super().__init__(db_config)

        self._config = db_config
        self._connection = None
        self._create_engine()
        self._cxn_manager = MySQLCxnManager(db_config.cxn_config)

    
    def execute(self, sql, *args, **kwargs):
        return self._cxn_manager.execute(sql, *args, **kwargs)
