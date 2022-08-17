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
        pool_pre_ping (bool): Performs liveliness check and expires all existing
            connections if the database is unreachable.

    """

    pool_size: Optional[int]
    pool_pre_ping: bool = True


class ModelDBConfig(ModelDBConfig):
    """Configuration for SQL connection using sqlalchemy.

    Args:
        host (str): Host of SQL server.
        port (str): Port of SQL server on host.
        user (str): User for connecting to SQL server.
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
    dialect_str: str = "mysql+pymysql"


class ModelDB(ModelDB):
    """DBService client responsible for handling connections to the model database."""

    def __init__(self, config: ModelDBConfig):
        """Initialize client service.

        Args:
            config (ModelDBConfig): Connection configuration.

        """
        self.config = config

        self._create_engine()

    def _create_engine(self) -> None:
        """Create sqlalchemy engine using uri."""
        self.pid = os.getpid()

        # since using a context manager, must have context-local managed vars
        self._connection = ContextVar("connection", default=None)

        self.engine = create_engine(
            f"{self.config.dialect_str}://{self.config.user}:%s@{self.config.host}:\
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
        logger.debug("ModelDB creating session.")
        with self.connection():
            session = self._sessionmaker()
            logger.debug("ModelDB session created.")
            session.expire_on_commit = False
            return session

    def execute(self, sql) -> list:
        """Execute sql inside a managed session.

        Args:
            sql (sqlalchemy.sql.base.Executable): SQL query to execute.

        Results:
            list: Results of query operation

        """
        logger.info("ModelDB executing: %s", str(sql))
        with self.session() as session:

            res = session.execute(sql)
            session.commit()

        logger.info("ModelDB executed: %s", str(sql))

        return res

    def select(self, sql: Select) -> list:
        """Execute sql query inside a managed session.

        Args:
            sql (Select): Selection query to execute.

        Results:
            list: Results of selection operation

        """
        logger.info("ModelDB selecting: %s", str(sql))
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
        logger.info("ModelDB inserting: %s", str(sql))
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
        logger.info("ModelDB inserting many: %s", [str(statement) for statement in sql])
        with self.session() as session:

            results = []

            for stmt in sql:
                res = session.execute(stmt)
                results.append(res)

            session.commit()

        logger.info("Sucessfully executed: %s", [str(statement) for statement in sql])

        return [res.inserted_primary_key for res in results]

    @classmethod
    def from_config_init(cls, **kwargs) -> "ModelDB":
        """Initialize database handler from ModelDBConfig kwargs."""
        config = ModelDBConfig(**kwargs)
        return cls(config=config)
