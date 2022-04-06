from abc import ABC, abstractmethod
from pydantic import BaseSettings
from typing import List
import logging

logger = logging.getLogger(__name__)

class DBServiceConfig(BaseSettings, ABC):
    ...

class DBService(ABC):

    target_field = "fingerprint"

    @abstractmethod
    def __init__(self, db_config: DBServiceConfig):
        ...
    
    @abstractmethod
    def insert_one(self):
        ...

    @abstractmethod
    def find(self):
        ...

