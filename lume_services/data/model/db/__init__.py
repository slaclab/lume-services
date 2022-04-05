from abc import ABC, abstractmethod
from pydantic import BaseSettings

from lume_services.data.model.db.schema import Base

class DBServiceConfig(BaseSettings, ABC):
    ...

class DBService(ABC):

    def __init__(self, db_config: DBServiceConfig):
        ...

    @abstractmethod
    def execute(self, orm_obj: Base):
        ...
        # Raise not implemented

    @abstractmethod
    def insert(self, orm_obj: Base):
        ...
        # Raise not implemented


    @abstractmethod
    def insert_many(self, orm_obj: Base):
        ...
        # Raise not implemented

