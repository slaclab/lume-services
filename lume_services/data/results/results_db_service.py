from typing import List
import json
import logging

from lume_services.data.results.db import DBService
from lume_services.utils import flatten_dict

from lume_services.data.results.db.document import ResultDocument
from lume_services.data.results.db.models import ModelDocs

from enum import Enum
import pandas as pd

logger = logging.getLogger(__name__)


class ResultsDBService:
    """Results database for use with NoSQL database service
    
    """

    def __init__(self, db_service: DBService, model_docs: Enum = ModelDocs):
        """Initialize Results DB Service interface

        Args:
            db_service (DBService): DB Connection service
            model_docs (Enum): Enum of configured model documents

        
        """
        self._db_service = db_service
        self._model_docs = model_docs

    def store(self, model_type: str, **kwargs) -> bool:
        """Store model data.

        Args:
            model_type (str): Must correspond to models listed in model_docs enum provided during construction
            **kwargs: Initialization arguments for document construction covering minimal data required by model

        Returns:
            bool: Success of storage operation

        """

        model_doc_type = self._get_model_doc_type(model_type)

        doc = model_doc_type(**kwargs)

        # validate document contruction
        try:
            doc.validate()

        except model_doc_type.get_validation_error() as err:
            logger.error("Unable to validate doc with type %s and kwargs= %s", model_doc_type.__name__, json.dumps(kwargs))
            raise err


        # insert
        res = self._db_service.insert_one(doc)

        # confirm success
        pk_id = res.get_pk_id()

        if pk_id:
            logger.info("Document stored with id %s", pk_id)
            return True
        
        else:
            return False

    def find(self, model_type: str, query={}, fields: List[str] = None) -> list:

        model_doc_type = self._get_model_doc_type(model_type)

        results = self._db_service.find(model_doc_type, query, fields)
        
        return list(results)

    def find_all(self, model_type: str) -> list:

        results = self._db_service.find_all(model_type)

        return list(results)

    def load_dataframe(self, *, model_type: str, query = {}, fields: List[str] = []) -> pd.DataFrame:
        # flattens results and returns dataframe
        results = self.find(model_type, query=query, fields=fields)
        flattened = [flatten_dict(res) for res in results]
        df = pd.DataFrame(flattened)

        # Load DataFrame
        df["date"] = pd.to_datetime(df["isotime"])
        df["_id"] = df["_id"].astype(str)

        return df


    def _get_model_doc_type(self, model_type: str) -> type[ResultDocument]:

        return ModelDocs[model_type].value
