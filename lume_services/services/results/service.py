from .db import ResultsDB

from typing import List
import logging

from lume_services.utils import get_jsonable_dict

logger = logging.getLogger(__name__)


class ResultsDBService:
    """Results database for use with NoSQL database service"""

    def __init__(self, results_db: ResultsDB):
        """Initialize Results DB Service interface
        Args:
            results_db (DBService): DB Connection service
        """
        self._results_db = results_db

    def insert_one(self, item: dict, **kwargs) -> str:
        """Store model data.
        Args:
            model_type (str): Must correspond to models listed in model_docs enum
                provided during construction.
            **kwargs: Initialization arguments for document construction covering
                minimal data required by model.
        Returns:
            bool: Success of storage operation
        """

        return self._results_db.insert_one(**item, **kwargs)

    def insert_many(self, items: List[dict], **kwargs) -> List[str]:
        """Insert many documents into the database.

        Args:
            items (List[dict]): List of dictionary representations of items

        Returns:
            List[str]: List of interted ids

        """
        return self._results_db.insert_many(items, **kwargs)

    def find(self, *, query: dict, fields: List[str] = None, **kwargs) -> List[dict]:
        """Find a document based on a query.

        Args:
            query (dict): fields to query on
            fields (List[str]): List of fields to return if any
            **kwargs (dict): DB implementation specific fields

        Returns:
            List[dict]: List of dict reps of found items.

        """
        query = get_jsonable_dict(query)
        return self._results_db.find(query=query, fields=fields, **kwargs)

    def find_all(self, **kwargs) -> List[dict]:
        """Find all documents for a collection

        Returns:
            List[dict]: List of result items represented as dict.
        """
        return self._results_db.find_all(**kwargs)
