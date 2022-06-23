import pytest
import mongomock
from datetime import datetime
from typing import List, Dict
from lume_services.data.files import HDF5File, ImageFile

from lume_services.services.data.results import (
    ResultsDBService,
    ResultsDB,
    MongodbResultsDBConfig,
)
from lume_services.services.data.results.mongodb import MongodbCollection
from pymongo import DESCENDING

from lume_services.data.results import get_collections, Result, ImpactResult
from lume_services.tests.files import SAMPLE_IMAGE_FILE, SAMPLE_IMPACT_ARCHIVE


class MongoMockResultsDB(ResultsDB):
    def __init__(self, db_config: MongodbResultsDBConfig):
        self._collections = {}
        self.config = db_config
        self._client = mongomock.MongoClient(**db_config.dict(exclude_none=True))

    def insert_one(self, collection: str, **kwargs) -> str:
        db = self._client[self.config.database]
        inserted_id = db[collection].insert_one(kwargs).inserted_id

        return inserted_id

    def insert_many(self, collection: str, items: List[dict]) -> List[str]:
        db = self._client[self.config.database]
        inserted_ids = db[collection].insert_many(items).inserted_ids

        return [inserted_id.str for inserted_id in inserted_ids]

    def find(
        self, collection: str, query: dict = None, fields: List[str] = None
    ) -> List[dict]:

        db = self._client[self.config.database]
        if fields is None:
            results = db[collection].find(query)
        else:
            results = db[collection].find(query, projection=fields)

        return list(results)

    def find_all(self, collection: str) -> List[dict]:
        return self.find(collection=collection)

    def configure(self, collections: Dict[str, List[str]]) -> None:

        db = self._client[self.config.database]
        for collection_name, index in collections.items():

            formatted_index = [(idx, DESCENDING) for idx in index]
            db[collection_name].create_index(formatted_index, unique=True)
            index_info = db[collection_name].index_information()

            self._collections[collection_name] = MongodbCollection(
                database=self.config.database, name=collection_name, indices=index_info
            )


@pytest.fixture(scope="session", autouse=True)
def mongodb_host(request):
    return request.config.getini("mysql_host")


@pytest.fixture(scope="session", autouse=True)
def mongodb_port(request):
    port = request.config.getini("mongodb_port")
    return int(port)


@pytest.fixture(scope="session", autouse=True)
def mongodb_database(request):
    return request.config.getini("mongodb_dbname")


@pytest.fixture(scope="session", autouse=True)
def mongodb_config(mongodb_host, mongodb_port, mongodb_database):
    return MongodbResultsDBConfig(
        host=mongodb_host, port=mongodb_port, database=mongodb_database
    )


@pytest.fixture(scope="session", autouse=True)
def mongodb_results_db(mongodb_config):
    return MongoMockResultsDB(mongodb_config)


@pytest.fixture(scope="class", autouse=True)
def results_db_service(mongodb_results_db, mongodb_database):

    collections = get_collections()
    mongodb_results_db.configure(collections=collections)

    results_db_service = ResultsDBService(results_db=mongodb_results_db)

    yield results_db_service

    results_db_service._results_db._client.drop_database(mongodb_database)


@pytest.fixture(scope="session", autouse=True)
def generic_result():
    return Result(
        flow_id="test_flow_id",
        inputs={"input1": 2.0, "input2": [1, 2, 3, 4, 5]},
        outputs={
            "output1": 2.0,
            "output2": [1, 2, 3, 4, 5],
        },
    )


@pytest.fixture(scope="session", autouse=True)
def impact_result():
    return ImpactResult(
        flow_id="test_flow_id",
        inputs={"input1": 2.0, "input2": [1, 2, 3, 4, 5], "input3": "my_file.txt"},
        outputs={
            "output1": 2.0,
            "output2": [1, 2, 3, 4, 5],
            "ouptut3": "my_file.txt",
        },
        plot_file=ImageFile(filename=SAMPLE_IMAGE_FILE, file_system_identifier="local"),
        archive=HDF5File(
            filename=SAMPLE_IMPACT_ARCHIVE, file_system_identifier="local"
        ),
        pv_collection_isotime=datetime.now(),
        config={"config1": 1, "config2": 2},
    )
