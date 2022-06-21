from .db import ResultsDB, ResultsDBConfig
from .mongodb import MongodbResultsDB, MongodbResultsDBConfig


from typing import List, Type
import json
import logging

from lume_services.utils import flatten_dict

from lume_services.config import LUMESettings

import pandas as pd

logger = logging.getLogger(__name__)


class ResultsServiceConfig(LUMESettings):
    model_docs: dict  # describes documents allowed


class ResultsService:
    """Results database for use with NoSQL database service"""

    def __init__(self, results_db: ResultsDB):
        """Initialize Results DB Service interface
        Args:
            results_dv (DBService): DB Connection service
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

        return self._results_db.insert_one(item, **kwargs)

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
        return self._results_db.find(query=query, fields=fields, **kwargs)

    def find_all(self, **kwargs) -> List[dict]:
        """Find all documents for a collection

        Returns:
            List[dict]: List of result items represented as dict.
        """
        return self._results_db.find_all(**kwargs)

    def load_dataframe(
        self, *, query={}, fields: List[str] = None, **kwargs
    ) -> pd.DataFrame:
        """Load dataframe from result database query.
        Args:
            query (dict): Field values for constructing query
            fields List[str]: Subset of fields to return
            **kwargs (dict): DB implementation specific fields
        Returns:
            pd.DataFrame
        """
        # flattens results and returns dataframe
        results = self.find(query=query, fields=fields, **kwargs)
        flattened = [flatten_dict(res) for res in results]
        df = pd.DataFrame(flattened)

        # Load DataFrame
        # df["date"] = pd.to_datetime(df["pv_collection_isotime"])
        #  df["_id"] = df["_id"].astype(str)

        return df
