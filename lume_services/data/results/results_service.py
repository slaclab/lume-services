from typing import List, Type
import json
import logging

from lume_services.data.results.db.db_service import DBService
from lume_services.utils import flatten_dict

from lume_services.data.results.db.document import DocumentBase

from lume_services.config import LUMESettings

from enum import Enum
import pandas as pd

logger = logging.getLogger(__name__)

class ResultsServiceConfig(LUMESettings):
    model_docs: Enum # describes documents allowed

class ResultsService:
    """Results database for use with NoSQL database service"""

    def __init__(self, db_service: DBService, model_docs: Enum):
        """Initialize Results DB Service interface

        Args:
            db_service (DBService): DB Connection service
            model_docs (Enum): Enum of configured model documents

        """
        self._db_service = db_service
        self._model_docs = model_docs

    def store(self, model_type: str, **kwargs) -> str:
        """Store model data.

        Args:
            model_type (str): Must correspond to models listed in model_docs enum provided during construction
            **kwargs: Initialization arguments for document construction covering minimal data required by model

        Returns:
            bool: Success of storage operation

        """

        model_doc_type = self._get_model_doc_type(model_type)
        doc = model_doc_type(**kwargs)

        # insert
        try:
            res = self._db_service.insert_one(doc)

        except model_doc_type.get_validation_error() as err:
            logger.error(
                "Unable to validate doc with type %s and kwargs= %s",
                model_doc_type.__name__,
                json.dumps(kwargs),
            )
            raise err

        # confirm success
        pk_id = res.get_pk_id()

        if pk_id:
            logger.info("Document stored with id %s", pk_id)
            return res

        else:
            return None

    def _find(self, model_doc_type, query={}, fields: List[str] = None) -> list:
        """Find model entries from doc type query.

        Args:
            model_doc_type (Type[DocumentBase]): Model document type
            query (dict): Field values for constructing query
            fields List[str]: Subset of fields to return

        Return:
            list: Results of query

        """
        return self._db_service.find(model_doc_type, query, fields)

    def find(self, model_type: str, query={}, fields: List[str] = None) -> list:
        """Find model entries by query.

        Args:
            model_type (str): Must correspond to models listed in model_docs enum provided during construction
            query (dict): Field values for constructing query
            fields List[str]: Subset of fields to return

        Return:
            list: Results of query

        """

        model_doc_type = self._get_model_doc_type(model_type)

        results = self._find(model_doc_type, query, fields)

        if results is not None:
            return results
        else:
            return []

    def find_by_index(self, model_type: str, **kwargs) -> List[str]:
        """Find model entries based on query.

        Args:
            model_type (str): Must correspond to models listed in model_docs enum provided during construction
            **kwargs: Field values for constructing document

        Return:
            List[str]: List of index fields

        """

        model_doc_type = self._get_model_doc_type(model_type)

        index_fields = model_doc_type.get_unique_result_index_fields()

        for field in index_fields:

            kwargs.get(field)

        query = {field: kwargs.get(field, None) for field in index_fields}
        if any([value is None for field, value in query.items()]):
            raise ValueError(
                f"Missing index field  for {model_type}. Requires {','.join(index_fields)}. Provided: {json.dumps(query)}"
            )

        results = self._find(model_doc_type, query)

        if results is not None:
            return results[0]
        else:
            return []

    def find_by_unique_field(self, model_type: str, unique_result_hash: str) -> DocumentBase:
        """Find model entry by unique index hash.

        Args:
            model_type (str): Must correspond to models listed in model_docs enum provided during construction
            unique_result_hash (str): Hash of unique index

        Return:
            DocumentBase

        """

        model_doc_type = self._get_model_doc_type(model_type)

        query = {model_doc_type.target_field: unique_result_hash}

        results = self._find(model_doc_type, query)

        if results is not None:
            return results[0]
        else:
            return []

    def get_unique_field(self, model_type: str) -> str:
        """Get unique field for model type

        Args:
            model_type (str): Must correspond to models listed in model_docs enum provided during construction

        Return:
            str

        """

        model_doc_type = self._get_model_doc_type(model_type)
        return model_doc_type.target_field


    def find_all(self, model_type: str) -> list:
        """Get all members of a model_type collection

        Args:
            model_type (str): Must correspond to models listed in model_docs enum provided during construction

        Return:
            list: Results of query

        """

        results = self._db_service.find_all(model_type)

        if results is not None:
            return results
        else:
            return []

    def load_dataframe(
        self, *, model_type: str, query={}, fields: List[str] = []
    ) -> pd.DataFrame:
        """Load dataframe from result database query.

        Args:
            model_type (str): Must correspond to models listed in model_docs enum provided during construction
            query (dict): Field values for constructing query
            fields List[str]: Subset of fields to return

        Returns:
            pd.DataFrame

        """
        # flattens results and returns dataframe
        results = self.find(model_type, query=query, fields=fields)
        flattened = [flatten_dict(res) for res in results]
        df = pd.DataFrame(flattened)

        # Load DataFrame
        # df["date"] = pd.to_datetime(df["pv_collection_isotime"])
        #  df["_id"] = df["_id"].astype(str)

        return df

    def _get_model_doc_type(self, model_type: str) -> Type[DocumentBase]:
        """Get model doc type reference from model string.

        Args:
            model_type: str

        Return:
            type: Document type


        """

        if not getattr(self._model_docs, model_type):
            logger.error(
                "Model type %s not a member of model doc types: %s",
                model_type,
                ",".join([e.key for e in self._model_docs]),
            )
            raise ValueError(
                "Model type %s not a member of model doc types: %s",
                model_type,
                ",".join([e.key for e in self._model_docs]),
            )

        return self._model_docs[model_type].value

    def validate_model_type(self, model_type: str) -> None:
        """Utility for checking whether model type is a member of the model doc enum.

        Args:
            model_type: str
        """
        try:
            self._get_model_doc_type(model_type)

        except ValueError as err:
            raise err

    def get_index_fields(self, model_type: str):
        """Get index fields for value.

        ...
        """

        model_doc_type = self._get_model_doc_type(model_type)

        return model_doc_type.get_unique_result_index_fields()