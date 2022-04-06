from typing import List
import os
from pymongo import MongoClient

from contextvars import ContextVar
from contextlib import contextmanager

from lume_services.data.results.db.service import DBService, DBServiceConfig
from mongoengine import Document

import mongoengine

class MongodbConfig(DBServiceConfig):
    db: str #name of database
    host: str 
    port: int
    #read_preference: str= ""
    username: str
    password: str
    #uuidRepresentation: str = 'pythonLegacy' # compat with pymongo 3.x
  #  authentication_source
  # authentication_mechanism
  # is_mock
  # kwargsfor example maxpoolsize, tz_aware, etc. See the documentation for pymongo’s MongoClient for a full list.


class MongodbService(DBService):
    # Note: pymongo is threadsafe

    def __init__(self, db_config: MongodbConfig):
        self.config = db_config

        # track pid to make multiprocessing safe
        self.pid = os.getpid()

        self._connection = ContextVar("connection", default=None)
        self._connect()


    def _connect(self) -> MongoClient:
        """Establish connection and set _connection.

        """
        mongoengine.connect(**self.config.dict())

        cxn = mongoengine.get_connection()
        self._connection.set(cxn)

        return cxn

    def _check_mp(self) -> None:
        """Check for multiprocessing. If PID is different that object PID, create new engine connection.

        """

        if os.getpid() != self.pid:
            self._connect()
    

    @property
    def _currect_connection(self) -> MongoClient:
        """Getter for current connection

        """

        return self._connection.get()


    @contextmanager
    def connection(self) -> MongoClient:
        #Context manager for operations. Will clean up connections on exit of
        #scope.
       

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
                    mongoengine.disconnect()
                    self._connection.set(None)


    def insert_one(self, doc: Document) -> Document:

        with self.connection() as cxn:
            res = doc.save(validate=True)

        return res


    def find(self, model_doc_type: type[Document], query: dict=None, fields: List[str] = None) -> List[Document]:

        with self.connection() as cxn:
            results = model_doc_type.objects(**query)

        if len(fields):
            results = results.only(*fields)

        return results

    def find_all(self, model_doc_type: type[Document]) -> List[Document]:

        with self.connection() as cxn:
            results = model_doc_type.object()

        return results 


    def disconnect(self):
        mongoengine.disconnect(alias="connected_db")

