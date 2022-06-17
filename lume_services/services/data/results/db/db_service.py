from abc import ABC, abstractmethod
from pydantic import BaseModel, root_validator
from typing import List, Type, Optional
import os
from matplotlib.pyplot import disconnect
from pymongo import MongoClient

from contextvars import ContextVar
from contextlib import contextmanager

from mongoengine import DynamicDocument, Document
from lume_services.config import LUMESettings

import logging
from urllib.parse import quote_plus


logger = logging.getLogger(__name__)


class DBServiceConfig(LUMESettings):
    ...


class DBService(ABC):
    """Implementation of the database service must translate the pydantic documents
    to database operations. 
    
    """
    @abstractmethod
    def __init__(self, db_config: DBServiceConfig):
        ...

    @abstractmethod
    def insert_one(self):
        ...

    @abstractmethod
    def find(self):
        ...

    @abstractmethod
    def find_all(self):
        ...


class MongoDBConfig(BaseModel):
    host: Optional[str]
    port: Optional[int]
    uri: Optional[str]
    tz_aware: Optional[bool]
    maxPoolSize: Optional[int]

    @root_validator(pre=True)
    def validate_config(cls, values):

        if not values.get("host") and not values.get("uri"):
            raise ValueError("Must provide host or uri")

        if values.get("password"):

            # require host, user, and password

            user = values.pop("user")
            password = values.pop("password")
            host = values.pop("host")


            values["uri"] =  "mongodb://%s:%s@%s" % (
            quote_plus(user), quote_plus(password), host)

        return values


class MongodbService(DBService):
    # Note: pymongo is threadsafe

    def __init__(self, db_config: MongoDBConfig):
        self.config = db_config

        # track pid to make multiprocessing safe
        self.pid = os.getpid()
        self._client = ContextVar("client", default=None)
        self._connect()

    def _connect(self) -> MongoClient:
        """Establish connection and set _client."""
        client = MongoClient(**self.config.dict(exclude_none=True))
        self._client.set(client)

        return client

    def _check_mp(self) -> None:
        """Check for multiprocessing. If PID is different that object PID, create new
        engine connection.

        """

        if os.getpid() != self.pid:
            self._connect()

    @property
    def _currect_connection(self) -> MongoClient:
        """Getter for current connection"""

        return self._client.get()

    def _disconnect(self):
        """Disconnect mongodb connection."""
        client = self._client.get()
        client.disconnect()
        self._client.set(None)

    def disconnect(self):
        """Disconnect mongodb connection."""
        self._disconnect()

    @contextmanager
    def client(self) -> MongoClient:
        """Context manager for mongoclient. Will check for multiprocessing and restart
        accordingly.

        """
        self._check_mp()

        # get connection
        client = self._client.get()

        if client is None:  # why clean up here? Hmm...
            client = self._connect()
            cleanup = True

        else:
            cleanup = False

        try:
            yield client

        finally:
            if cleanup:
                client = self._client.get()

                if client:
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
        self, *, collection, query: dict, fields: List[str] = None
    ) -> List[Document]:
        """Find a document based on a query.

        Args:
            collection (str): Document type to query
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
