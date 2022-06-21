import os
from pydantic import root_validator, Field
from typing import List, Optional
from urllib.parse import quote_plus

from pymongo import MongoClient

from contextvars import ContextVar
from contextlib import contextmanager

from lume_services.services.data.results.db import (
    ResultsDBServiceConfig,
    ResultsDBService,
)

import logging


logger = logging.getLogger(__name__)


class MongodbResultsDBConfig(ResultsDBServiceConfig):
    # excluded in serialization bc not used to initialize cxn
    database: str = Field(exclude=True)
    user: Optional[str]
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

            values["uri"] = "mongodb://%s:%s@%s" % (
                quote_plus(user),
                quote_plus(password),
                host,
            )

        return values


class MongodbResultsDBService(ResultsDBService):
    # Note: pymongo is threadsafe

    def __init__(self, db_config: MongodbResultsDBConfig):
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

    def insert_one(self, *, collection: str, **kwargs) -> str:
        """Insert one document into the database.

        Args:
            collection (str): Name of collection for saving document
            **kwargs: Kwargs contain representation of document

        Returns:
            str: saved document id

        """
        with self.connection() as client:
            db = client[self.config.database]
            inserted_id = db[collection].insert_one(kwargs).inserted_id

        return inserted_id

    def insert_many(self, *, collection: str, items: List[dict]) -> List[str]:
        """Insert many documents into the database.

        Args:
            collection (str): Document type to query
            items (List[dict]): List of dictionary reps of documents to save to database

        Returns:
            List[str]: List of saved document ids.

        """
        with self.connection() as client:
            db = client[self.config.database]
            inserted_ids = db[collection].insert_many(items).inserted_ids

        return [inserted_id.str for inserted_id in inserted_ids]

    def find(
        self, *, collection: str, query: dict, fields: List[str] = None
    ) -> List[dict]:
        """Find a document based on a query.

        Args:
            collection (str): Document type to query
            query (dict): Query in dictionary form mapping fields to values
            fields (List[str]): List of fields for filtering result

        Returns:
            List[dict]: List of of saved document ids.

        """

        with self.connection() as client:
            db = client[self.config.database]
            if fields is None:
                results = db[collection].find(query)
            else:
                results = db[collection].find(query, projection=fields)

        return results

    def find_all(self, *, collection: str) -> List[dict]:
        """Find all documents for a collection

        Args:
            collection (str): Collection name to query

        Returns:
            List[dict]: List of result documents.

        """
        return self.find(collection=collection)
