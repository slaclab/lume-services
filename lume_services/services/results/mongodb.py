import os
from pydantic import SecretStr, Field
from typing import List, Optional, Dict

from pymongo import DESCENDING, MongoClient
from pydantic import BaseModel

from contextvars import ContextVar
from contextlib import contextmanager

from lume_services.services.results.db import (
    ResultsDBConfig,
    ResultsDB,
)

import logging


logger = logging.getLogger(__name__)


class MongodbResultsDBConfig(ResultsDBConfig):
    """Configuration for connecting to Mongodb using the PyMongo driver.

    Attr:
        database (Optional[str]): Database name used for storing results.
        host (str): Host name of mongodb service.
        username (str): Username string.
        password (SecretStr): Password stored as a Pydantic secret string. https://pydantic-docs.helpmanual.io/usage/types/#secret-types
        port (int): Host port of mongodb service endpoint.
        authMechanism (): Auth mechanism supported by PyMongo driver. See https://pymongo.readthedocs.io/en/stable/api/pymongo/database.html#pymongo.auth.MECHANISMS.
        options (dict): Dictionary of additional connection options for MongoClient. https://pymongo.readthedocs.io/en/stable/api/pymongo/mongo_client.html#pymongo.mongo_client.MongoClient

    """  # noqa

    # excluded in serialization bc not used to initialize cxn
    database: Optional[str] = Field(exclude=True)
    username: str
    host: str
    password: SecretStr = Field(exclude=True)
    port: int
    authMechanism: str = "DEFAULT"
    # Pydantic literal parsing from env has issue with literals...
    # Literal["DEFAULT", 'GSSAPI', 'MONGODB-AWS', 'MONGODB-CR', 'MONGODB-X509',
    # 'PLAIN', 'SCRAM-SHA-1', 'SCRAM-SHA-256'] = "DEFAULT"
    options: dict = Field({}, exclude=True)

    class Config:
        allow_population_by_field_name = True


class MongodbCollection(BaseModel):
    database: str
    name: str
    # index info
    indices: dict


class MongodbResultsDB(ResultsDB):
    # Note: pymongo is threadsafe

    def __init__(self, db_config: MongodbResultsDBConfig, connect: bool = True):
        self.config = db_config

        # track pid to make multiprocessing safe
        self._pid = os.getpid()
        self._client = ContextVar("client", default=None)
        self._collections = ContextVar("collections", default={})
        if connect:
            self._connect()

    def _connect(self) -> MongoClient:
        """Establish connection and set _client."""

        client = MongoClient(
            **self.config.dict(exclude_none=True, by_alias=True),
            password=self.config.password.get_secret_value(),
            **self.config.options
        )

        self._client.set(client)
        db = client[self.config.database]

        collections = {}

        for collection_name in db.list_collection_names():
            collection = db[collection_name]
            index_info = collection.index_information()
            collections[collection_name] = MongodbCollection(
                database=self.config.database, name=collection_name, indices=index_info
            )

        self._collections.set(collections)

        return client

    def _check_mp(self) -> None:
        """Check for multiprocessing. If PID is different that object PID, create new
        engine connection.

        """

        if os.getpid() != self._pid:
            self._connect()

    @property
    def _currect_connection(self) -> MongoClient:
        """Getter for current connection"""

        return self._client.get()

    def _disconnect(self):
        """Disconnect mongodb connection."""
        client = self._client.get()
        if client is not None:
            client.disconnect()
        self._client.set(None)
        self._collections.set(None)

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

        if client is None:
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

    def insert_one(self, collection: str, **kwargs) -> str:
        """Insert one document into the database.

        Args:
            collection (str): Name of collection for saving document
            **kwargs: Kwargs contain representation of document

        Returns:
            str: saved document id

        """
        with self.client() as client:
            db = client[self.config.database]
            inserted_id = db[collection].insert_one(kwargs).inserted_id

        return inserted_id

    def insert_many(self, collection: str, items: List[dict]) -> List[str]:
        """Insert many documents into the database.

        Args:
            collection (str): Document type to query
            items (List[dict]): List of dictionary reps of documents to save to database

        Returns:
            List[str]: List of saved document ids.

        """
        with self.client() as client:
            db = client[self.config.database]
            inserted_ids = db[collection].insert_many(items).inserted_ids

        return [inserted_id.str for inserted_id in inserted_ids]

    def find(
        self, collection: str, query: dict = None, fields: List[str] = None
    ) -> List[dict]:
        """Find a document based on a query.

        Args:
            collection (str): Document type to query
            query (dict): Query in dictionary form mapping fields to values
            fields (List[str]): List of fields for filtering result

        Returns:
            List[dict]: List of of saved document ids.

        """

        with self.client() as client:
            db = client[self.config.database]
            if fields is None:
                results = db[collection].find(query)

            else:
                results = db[collection].find(query, projection=fields)

        return list(results)

    def find_all(self, collection: str) -> List[dict]:
        """Find all documents for a collection

        Args:
            collection (str): Collection name to query

        Returns:
            List[dict]: List of result documents.

        """
        return self.find(collection=collection)

    def configure(self, collections: Dict[str, List[str]]) -> None:
        """Configure the results database from collections and their indices.

        Args:
            collections (Dict[str, List[str]]): Dictionary mapping collection to
                index rep.

        """

        with self.client() as client:
            db = client[self.config.database]

            for collection_name, index in collections.items():

                formatted_index = [(idx, DESCENDING) for idx in index]
                db[collection_name].create_index(formatted_index, unique=True)

        for collection_name in collections:
            index_info = db[collection_name].index_information()

            collections[collection_name] = MongodbCollection(
                database=self.config.database, name=collection_name, indices=index_info
            )

        self._collections.set(collections)
