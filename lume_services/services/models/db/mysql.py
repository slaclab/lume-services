import os
import logging

from contextvars import ContextVar
from contextlib import contextmanager
from pydantic import BaseModel, SecretStr, Field

from sqlalchemy import create_engine
from sqlalchemy.sql.expression import Insert, Select
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine.base import Connection

from typing import List, Union, Optional

from urllib.parse import quote_plus
from lume_services.services.models.db.db import ModelDBConfig, ModelDB

logger = logging.getLogger(__name__)


class ConnectionConfig(BaseModel):
    """Configuration for creating sqlalchemy engine.

    Args:
        pool_size (int): Number of connections to maintain in the connection pool.
            Establishing connections is expensive and maintaining multiple connections
            in a pool allows for availability.
        pool_pre_ping (bool):

    """

    pool_size: Optional[int]
    pool_pre_ping: bool = True


class MySQLModelDBConfig(ModelDBConfig):
    """Configuration for MySQL connection.

    Args:
        host (str): Host of MySQL server.
        port (str): Port of MySQL server on host.
        user (str): User for connecting to MySQL server.
        password (SecretStr): Password for auth.
        database (str): Name of database.
        connection (ConnectionConfig): Configuration options for creating sqlalchemy
            engine.

    """

    host: str
    port: int
    user: str
    password: SecretStr = Field(exclude=True)
    database: str
    connection: ConnectionConfig = ConnectionConfig()


class MySQLModelDB(ModelDB):
    """MySQL implementation of the DBService client, allowing for Model DB connections
    to MySQL model db.

    """

    def __init__(self, config: MySQLModelDBConfig):
        """Initialize MySQL client service.

        Args:
            config (MySQLModelDBConfig): MySQL connection config

        """
        self.config = config

        self._create_engine()

    def _create_engine(self) -> None:
        """Create sqlalchemy engine using uri."""
        self.pid = os.getpid()

        # since using a context manager, must have context-local managed vars
        self._connection = ContextVar("connection", default=None)

        # pool_pre_ping provides liveliness check
        self.engine = create_engine(
            f"mysql+pymysql://{self.config.user}:%s@{self.config.host}:\
                {self.config.port}/{self.config.database}"
            % quote_plus(self.config.password.get_secret_value()),
            **self.config.connection.dict(exclude_none=True),
        )

        # sessionmaker for orm operations
        self._sessionmaker = sessionmaker(bind=self.engine)

    def _connect(self) -> Connection:
        """Establish connection and set _connection."""
        cxn = self.engine.connect()
        self._connection.set(cxn)

        return cxn

    def _check_mp(self) -> None:
        """Check for multiprocessing. If PID is different that object PID, create new
        engine connection.

        """

        if os.getpid() != self.pid:
            self._create_engine()

    @property
    def _currect_connection(self) -> Connection:
        """Getter for current connection"""

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
        logger.debug("MySQLModelDB creating session.")
        with self.connection():
            session = self._sessionmaker()
            logger.debug("MySQLModelDB session created.")
            session.expire_on_commit = False
            return session

    def execute(self, sql) -> list:
        """Execute sql inside a managed session.

        Args:
            sql (sqlalchemy.sql.base.Executable): SQL query to execute.

        Results:
            list: Results of query operation

        """
        logger.info("MySQLModelDB executing: %s", str(sql))
        with self.session() as session:

            res = session.execute(sql)
            session.commit()

        logger.info("MySQLModelDB executed: %s", str(sql))

        return res

    def select(self, sql: Select) -> list:
        """Execute sql query inside a managed session.

        Args:
            sql (Select): Selection query to execute.

        Results:
            list: Results of selection operation

        """
        logger.info("MySQLModelDB selecting: %s", str(sql))
        with self.session() as session:

            res = session.execute(sql).scalars().all()
            session.commit()

        return res

    def insert(self, sql: Insert):
        """Execute and insert operation inside a managed session.

        Args:
            sql (Insert): Sqlalchemy insert operation

        Returns:
            Union[str, int]: primary key returned from insert operation

        """
        logger.info("MySQLModelDB inserting: %s", str(sql))
        with self.session() as session:

            res = session.execute(sql)
            session.commit()

        logger.info("Sucessfully executed: %s", str(sql))

        return res.inserted_primary_key

    def insert_many(self, sql: List[Insert]) -> List[Union[str, int]]:
        """Execute many inserts within a managed session.

        Args:
            sql (List[Insert]): Execute a sqlalchemy insert operation

        Returns:
            List[Union[str, int]]: List of primary keys returned from insert operation

        """
        logger.info(
            "MySQLModelDB inserting many: %s", [str(statement) for statement in sql]
        )
        with self.session() as session:

            results = []

            for stmt in sql:
                res = session.execute(stmt)
                results.append(res)

            session.commit()

        logger.info("Sucessfully executed: %s", [str(statement) for statement in sql])

        return [res.inserted_primary_key for res in results]

    @classmethod
    def from_config_init(cls, **kwargs) -> "MySQLModelDB":
        """Initialize database handler from MySQLModelDBConfig kwargs."""
        config = MySQLModelDBConfig(**kwargs)
        return cls(config=config)
