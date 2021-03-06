from abc import ABC, abstractclassmethod, abstractmethod
from typing import List
import logging

from pydantic import BaseModel
from sqlalchemy.sql.base import Executable
from sqlalchemy.sql.expression import Insert, Select

logger = logging.getLogger(__name__)


class ModelDBConfig(BaseModel):
    ...


class ModelDB(ABC):
    @abstractmethod
    def __init__(self, db_config: ModelDBConfig):
        ...

    @abstractmethod
    def execute(self, statement: Executable):
        """Generic execution method for statements.

        Args:
            statement(Executable): An executable statement (select, insert...)
        """
        ...

    @abstractmethod
    def select(self, statement: Select):
        """Method for executing selection statements.

        Args:
            statement (Select): Executable selection statement.

        """
        ...

    @abstractmethod
    def insert(self, statement: Insert):
        """Method for executing insert statements.

        Args:
            statement (Insert): Executable insert statement.

        """
        ...

    @abstractmethod
    def insert_many(self, table_row_obj: List[Insert]):
        """Method accepting list of Insert statements. This is distinguished from the
        base insert method because many services will use context managment for the
        management of their sessions.

        Args:
            List[Insert]: List of executable insert statements.

        """
        ...

    @abstractclassmethod
    def from_config_init(cls, *args, **kwargs):
        """Convenience function for initializing config and db."""
