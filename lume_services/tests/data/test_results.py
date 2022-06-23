from datetime import datetime
import pytest
from PIL import Image
from lume_services.data.results import (
    GenericResult,
    ImpactResult,
    get_result_from_string,
)
from lume_services.tests.files import SAMPLE_IMPACT_ARCHIVE, SAMPLE_IMAGE_FILE
from lume_services.services.data.results import MongodbResultsDBConfig, MongodbResultsDB
from lume_services.data.results import get_collections
from pymongo.errors import DuplicateKeyError


@pytest.mark.parametrize(
    ("string", "result_class_target"),
    [
        ("lume_services.data.results.generic:GenericResult", GenericResult),
        ("lume_services.data.results.impact:ImpactResult", ImpactResult),
        pytest.param(
            "incorrect.import.string",
            GenericResult,
            marks=pytest.mark.xfail(strict=True),
        ),
    ],
)
def test_get_result_from_string(string, result_class_target):
    result_type = get_result_from_string(string)
    assert result_type == result_class_target


class TestGenericResult:
    def test_create_generic_result_from_alias(self):
        GenericResult(
            collection="generic",
            flow_id="test_flow_id",
            inputs={"input1": 4, "input2": 3},
            outputs={"output1": 1},
        )

    def test_to_json(self, generic_result):
        generic_result.json()

    def test_from_json(self, generic_result):
        json_rep = generic_result.json()
        GenericResult.parse_raw(json_rep)

    def test_from_jsonable_dict(self, generic_result):
        jsonable_dict = generic_result.jsonable_dict()
        GenericResult(**jsonable_dict)


class TestImpactResult:
    def create_impact_result_from_alias(self):
        """Impact result fixture"""
        return ImpactResult(
            collection="impact",
            flow_id="test_flow_id",
            inputs={"input1": 4, "input2": 3},
            outputs={"output1": 1},
            archive={
                "filename": SAMPLE_IMPACT_ARCHIVE,
                "file_system_identifier": "local",
            },
            plot_file={
                "filename": SAMPLE_IMAGE_FILE,
                "file_system_identifier": "local",
            },
            pv_collection_isotime=datetime.utcnow(),
            config={"example_config": 1},
        )

    def test_to_json(self, impact_result):
        impact_result.json()

    def test_from_json(self, impact_result):
        json_rep = impact_result.json()
        ImpactResult.parse_raw(json_rep)

    def test_from_jsonable_dict(self, impact_result):
        jsonable_dict = impact_result.jsonable_dict()
        ImpactResult(**jsonable_dict)

    def test_load_image(self, impact_result, context):
        image = impact_result.plot_file.read(context.file_service())
        assert isinstance(image, (Image.Image,))


class TestMongodbResultsDBConfig:
    def test_construction_to_uri(self):
        config = MongodbResultsDBConfig(
            database="results",
            host="localhost",
            user="user",
            port=3030,
            password="test",
        )

        assert not config.user
        assert config.uri is not None


class TestMongodbResultsDB:
    def test_collections_mockmongo(self, results_db_service):
        # check collections represented in results service db
        collections = get_collections()
        assert all(
            [
                collection_name in results_db_service._results_db._collections
                for collection_name in collections.keys()
            ]
        )

    def test_mongo_results_db_init(self, mongodb_config):
        MongodbResultsDB(mongodb_config, connect=False)


class TestResultsDBService:
    def test_generic_result_insert_by_service(self, generic_result, results_db_service):
        test_generic_result_insert = results_db_service.insert_one(
            generic_result.jsonable_dict()
        )
        assert test_generic_result_insert is not None

        # confirm duplicate raises error
        with pytest.raises(DuplicateKeyError):
            test_generic_result_insert = results_db_service.insert_one(
                generic_result.jsonable_dict()
            )

    def test_impact_result_insert_by_service(self, impact_result, results_db_service):

        test_impact_result_insert = results_db_service.insert_one(
            impact_result.jsonable_dict()
        )
        assert test_impact_result_insert is not None

        # confirm duplicate raises error
        with pytest.raises(DuplicateKeyError):
            test_impact_result_insert = results_db_service.insert_one(
                impact_result.jsonable_dict()
            )


class TestResultsInsertMethods:
    def test_generic_result_insert_by_method(self, generic_result, results_db_service):
        generic_result.insert(results_db_service=results_db_service)

        # confirm duplicate raises error
        with pytest.raises(DuplicateKeyError):
            generic_result.insert(results_db_service=results_db_service)

    def test_impact_result_insert_by_method(self, impact_result, results_db_service):
        impact_result.insert(results_db_service=results_db_service)

        # confirm duplicate raises error
        with pytest.raises(DuplicateKeyError):
            impact_result.insert(results_db_service=results_db_service)
