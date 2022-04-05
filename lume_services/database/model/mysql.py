from pydantic import BaseSettings

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.sql.expression import Insert, Select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.base import Connection
import os

from lume_services.database.model.db import DBServiceConfig, DBService

from pkg_resources import resource_filename
from contextvars import ContextVar
from contextlib import contextmanager


MYSQL_MODEL_SCHEMA = resource_filename("lume_services.database.model", "schema.sql")


class MySQLConfig(DBServiceConfig):
    db_uri: str
    pool_size: int



"""
https://docs.sqlalchemy.org/en/14/dialects/mysql.html#create-table-arguments-including-storage-engines
mysql_engine='InnoDB',
      mariadb_engine='InnoDB',

      mysql_charset='utf8mb4',
      mariadb_charset='utf8',"""

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
        self.engine = create_engine(self.config.db_uri, *connect_args, pool_pre_ping=True, pool_size=self.config.pool_size)

        # sessionmaker for orm operations
        self._sessionmaker = sessionmaker(bind=self.engine)

    def _connect(self) -> Connection:
        cxn = self.engine.connect()
        self._connection.set(cxn)

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

    def session(self):
        with self.connection() as cxn:
            session = self._sessionmaker()
            session.expire_on_commit = False
            return session


    def execute(self, sql: Select):
        with self.session() as session:

            res = session.execute(sql).scalars().all()
            session.commit()

        return res

    def insert(self, sql: Insert):
        with self.session() as session:

            res = session.execute(sql)
            session.commit() 

        return res.inserted_primary_key

