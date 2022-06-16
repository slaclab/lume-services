from typing import List, Type
import os
from pymongo import MongoClient

from contextvars import ContextVar
from contextlib import contextmanager

from lume_services.services.data.results.db.db_service import DBService, DBServiceConfig
from mongoengine import Document

import mongoengine


class MongodbConfig(DBServiceConfig):
    db: str  # name of database
    host: str
    port: int
    # read_preference: str= ""
    username: str
    password: str
    # uuidRepresentation: str = 'pythonLegacy' # compat with pymongo 3.x


#  authentication_source
# authentication_mechanism
# is_mock
# kwargsfor example maxpoolsize, tz_aware, etc. See the documentation for pymongo’s
# MongoClient for a full list.


class MongodbService(DBService):
    # Note: pymongo is threadsafe

    def __init__(self, db_config: MongodbConfig):
        self.config = db_config

        # track pid to make multiprocessing safe
        self.pid = os.getpid()

        self._connection = ContextVar("connection", default=None)
        self._connect()

    def _connect(self) -> MongoClient:
        """Establish connection and set _connection."""
        mongoengine.connect(**self.config.dict())

        cxn = mongoengine.get_connection()
        self._connection.set(cxn)

        return cxn

    def _check_mp(self) -> None:
        """Check for multiprocessing. If PID is different that object PID, create new
        engine connection.

        """

        if os.getpid() != self.pid:
            self._connect()

    @property
    def _currect_connection(self) -> MongoClient:
        """Getter for current connection"""

        return self._connection.get()

    def _disconnect(self):
        """Disconnect mongodb connection."""
        mongoengine.disconnect()
        self._connection.set(None)

    def disconnect(self):
        """Disconnect mongodb connection."""
        self._disconnect()

    @contextmanager
    def connection(self) -> MongoClient:
        """Context manager for mongoclient. Will check for multiprocessing and restart
        accordingly.

        """
        self._check_mp()

        # get connection
        cxn = self._connection.get()

        if cxn is None:  # why clean up here? Hmm...
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
                    self._disconnect()

    def insert_one(self, doc: Document) -> Document:
        """Insert one document into the database.

        Args:
            doc (Document): Document to save

        Returns:
            Document: Saved document

        """
        with self.connection():
            res = doc.save(validate=True)

        return res

    def find(
        self, model_doc_type: Type[Document], query: dict, fields: List[str] = None
    ) -> List[Document]:
        """Find a document based on a query.

        Args:
            model_doc_type (Type[Document]): Document type to query
            query (dict): Query in dictionary form of field to value
            fields (List[str]): List of fields for filtering result

        Returns:
            List[Document]: List of query result documents.

        """

        with self.connection():
            results = model_doc_type.objects(**query)

        if fields is not None and len(fields):
            results = results.only(*fields)

        return results

    def find_all(self, model_doc_type: type[Document]) -> List[Document]:
        """Find all documents for a model type.

        Args:
            model_doc_type (type[Document]): Document type to query
            query (dict): Query in dictionary form of field to value
            fields (List[str]): List of fields for filtering result

        Returns:
            List[Document]: List of query result documents.

        """

        with self.connection():
            results = model_doc_type.objects()

        return results
