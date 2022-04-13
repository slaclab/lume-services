import os
import logging

from contextvars import ContextVar
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.sql.expression import Insert, Select
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine.base import Connection

from typing import List

from lume_services.data.model.db.db_service import DBServiceConfig, DBService


logger = logging.getLogger(__name__)


class MySQLConfig(DBServiceConfig):
    """Configuration for MySQL connection.

    db_uri: uri for establishing db connection
    pool_size: Number of connections to maintain in the connection pool. Establishing connections is expensive and 
    maintaining multiple connections in a pool allows for availability.
    
    """
    db_uri: str
    pool_size: int


class MySQLService(DBService):
    """MySQL implementation of the DBService client, allowing for Model DB connections to MySQL model db.
    
    """

    def __init__(self, config: MySQLConfig):
        """Initialize MySQL client service.

        Args:
            config (MySQLConfig): MySQL connection config
        
        """
        self.config = config
        self._create_engine()


    def _create_engine(self) -> None:
        """Create sqlalchemy engine using db_uri.
        
        """
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
        """Establish connection and set _connection.

        """
        cxn = self.engine.connect()
        self._connection.set(cxn)

        return cxn

    def _check_mp(self) -> None:
        """Check for multiprocessing. If PID is different that object PID, create new engine connection.

        """

        if os.getpid() != self.pid:
            self._create_engine()
    

    @property
    def _currect_connection(self) -> Connection:
        """Getter for current connection

        """

        return self._connection.get()


    @contextmanager
    def connection(self) -> Connection:
        """Context manager for operations. Will clean up connections on exit of
        scope.
        """

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


    def session(self) -> Session:
        """Establishes Session with active connection. 

        Note: Setting expire_on_commit to False allows us to access objects
        after session closing.
        
        """
        with self.connection() as cxn:
            session = self._sessionmaker()
            session.expire_on_commit = False
            return session

    def execute(self, sql) -> list:
        """Execute sql inside a managed session.

        Args:
            sql: Execute a query

        Results:
            list: Results of query operation

        """
        with self.session() as session:

            res = session.execute(sql)
            session.commit()

        return res



    def select(self, sql: Select) -> list:
        """Execute sql query inside a managed session.

        Args:
            sql: Execute a selection query

        Results:
            list: Results of selection operation

        """
        with self.session() as session:

            res = session.execute(sql).scalars().all()
            session.commit()

        return res

    def insert(self, sql: Insert):
        """Execute and insert operation inside a managed session.
        
        Args:
            sql (Insert): Execute a sqlalchemy insert operation

        Returns:
            primary key returned from insert operation

        """
        with self.session() as session:

            res = session.execute(sql)
            session.commit() 

        return res.inserted_primary_key

    def insert_many(self, sql: List[Insert]):
        """Execute many inserts within a managed session.
        
        Args:
            sql (List[Insert]): Execute a sqlalchemy insert operation

        Returns:
            list of primary keys returned from insert operation

        """

        with self.session() as session:

            results = []

            for stmt in sql:
                res = session.execute(stmt)
                results.append(res)

            session.commit() 

        return [res.inserted_primary_key for res in results]
