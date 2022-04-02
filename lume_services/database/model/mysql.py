from pydantic import BaseSettings

from contextlib import contextmanager

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine.base import Connection
import os

from lume_services.database.model.db import DBServiceConfig, DBService

from pkg_resources import resource_filename
from contextvars import ContextVar
from contextlib import contextmanager


MYSQL_MODEL_SCHEMA = resource_filename("lume_services.database.model", "schema.sql")
# guesses: r.successful, r.dict


class MySQLConfig(DBServiceConfig):
    db_uri: str
    pool_size: int


class MySQLService(DBService):

    def __init__(self, config: MySQLConfig):
        super().__init__(config)
        self.config = config
        self._create_engine()


    def _create_engine(self):
        self.pid = os.getpid()

        # can possible pass args here...
        connect_args = {}

        # since using a context manager, must have context-local managed vars
        self._connection = ContextVar("connection", default=None)

        # pool_pre_ping provides liveliness check
        self._engine = create_engine(self.config.db_uri, *connect_args, pool_pre_ping=True, pool_size=self.config.pool_size)

        # don't really need now
        # create a scoped session
        # self.orm_sessionmaker = sessionmaker(bind=self.engine)
        #self.session = scoped_session(self.orm_sessionmaker)

    def _connect(self) -> Connection:
        cxn = self._engine.connect()
        self._connection.set(cxn)
       # self._inspector = inspect(self._engine)
        return cxn

    def _check_mp(self):

        # check pid against object pid and create new engine in event of another process
        if os.getpid() != self.pid:
            self._create_engine()
    

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
            cxn = self._connect()
            cleanup = True

        else:
            cleanup = False

        try:
            yield cxn

        finally:
            if cleanup:
                cxn = self._connection.get()

                if cxn:
                    cxn.close()
                    self._connection.set(None)


    def execute(self, sql, *args, **kwargs):
        with self.connection() as cxn:
            
            r = cxn.execute(sql, *args, **kwargs)

            return r
