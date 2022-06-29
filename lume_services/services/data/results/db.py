from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import List


import logging


logger = logging.getLogger(__name__)


class ResultsDBConfig(BaseModel):
    ...


class ResultsDB(ABC):
    """Implementation of the database."""

    @abstractmethod
    def __init__(self, db_config: ResultsDBConfig):
        ...

    @abstractmethod
    def insert_one(self, item: dict, **kwargs) -> str:
        """Insert document into the database.

        Args:
            item (dict): Dictionary representation of item

        Returns:
            str: Inserted item id

        """

    @abstractmethod
    def insert_many(self, items: List[dict], **kwargs) -> List[str]:
        """Insert many documents into the database.

        Args:
            items (List[dict]): List of dictionary representations of items

        Returns:
            List[str]: List of interted ids

        """

    @abstractmethod
    def find(self, *, query: dict, fields: List[str] = None, **kwargs) -> List[dict]:
        """Find a document based on a query.

        Args:
            query (dict): fields to query on
            fields (List[str]): List of fields to return if any
            **kwargs (dict): DB implementation specific fields

        Returns:
            List[dict]: List of dict reps of found items.

        """

    @abstractmethod
    def find_all(self, **kwargs) -> List[dict]:
        """Find all documents for a collection

        Returns:
            List[dict]: List of result items represented as dict.
        """

    @abstractmethod
    def configure(self, **kwargs) -> None:
        """Configure the results db service."""
