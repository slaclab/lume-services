from abc import ABC, abstractmethod
from pydantic import BaseSettings
from typing import List

from sqlalchemy.sql.base import Executable
from sqlalchemy.sql.expression import Insert, Select

from lume_services.data.model.db.schema import Base

class DBServiceConfig(BaseSettings, ABC):
    ...

class DBService(ABC):

    @abstractmethod
    def __init__(self, db_config: DBServiceConfig):
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
        """Method accepting list of Insert statements. This is distinguished form the base insert method because 
        many services will use context managment for the management of their sessions.

        Args:
            List[Insert]: List of executable insert statements.

        """
        ...
