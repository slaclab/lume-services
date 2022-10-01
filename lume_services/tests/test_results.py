from datetime import datetime
import pytest
import numpy as np
import pandas as pd
from PIL import Image
from pydantic import ValidationError
from pymongo.errors import DuplicateKeyError

from lume_services.results import (
    Result,
    ImpactResult,
    get_result_from_string,
)
from lume_services.results.generic import load_db_dict, get_bson_dict
from lume_services.files import HDF5File, ImageFile
from lume_services.tests.files import SAMPLE_IMPACT_ARCHIVE, SAMPLE_IMAGE_FILE
from lume_services.services.results import MongodbResultsDBConfig, MongodbResultsDB


@pytest.fixture(scope="module", autouse=True)
def impact_result(results_db_service):
    result = ImpactResult(
        project_name="impact",
        flow_id="test_flow_id_impact",
        inputs={
            "input1": 2.0,
            "input2": np.array([1, 2, 3, 4, 5]),
            "input3": "my_file.txt",
        },
        outputs={
            "output1": 2.0,
            "output2": np.array([1, 2, 3, 4, 5]),
            "output3": "my_file.txt",
        },
        plot_file=ImageFile(filename=SAMPLE_IMAGE_FILE, filesystem_identifier="local"),
        archive=HDF5File(filename=SAMPLE_IMPACT_ARCHIVE, filesystem_identifier="local"),
        pv_collection_isotime=datetime.now(),
        config={"config1": 1, "config2": 2},
    )

    rep = result.get_db_dict()
    insert_rep = results_db_service.insert_one(rep)
    assert insert_rep is not None
    return result


def check_impact_result_equal(impact_result, new_impact_obj):
    assert impact_result.flow_id == new_impact_obj.flow_id
    assert impact_result.inputs["input1"] == new_impact_obj.inputs["input1"]
    assert isinstance(new_impact_obj.inputs["input2"], np.ndarray)
    assert np.array_equal(
        impact_result.inputs["input2"], new_impact_obj.inputs["input2"]
    )
    assert impact_result.inputs["input3"] == new_impact_obj.inputs["input3"]
    assert impact_result.outputs["output1"] == new_impact_obj.outputs["output1"]
    assert isinstance(new_impact_obj.outputs["output2"], np.ndarray)
    assert np.array_equal(
        impact_result.outputs["output2"], new_impact_obj.outputs["output2"]
    )
    assert impact_result.outputs["output3"] == new_impact_obj.outputs["output3"]
    assert impact_result.archive == new_impact_obj.archive
    assert impact_result.plot_file == new_impact_obj.plot_file
    assert impact_result.pv_collection_isotime == new_impact_obj.pv_collection_isotime
    assert impact_result.config == new_impact_obj.config


@pytest.fixture(scope="module", autouse=True)
def generic_result(results_db_service):
    result = Result(
        project_name="generic",
        flow_id="test_flow_id",
        inputs={"input1": 2.0, "input2": np.array([1, 2, 3, 4, 5])},
        outputs={
            "output1": 2.0,
            "output2": pd.DataFrame({"x": [0, 1, 2], "y": [1, 2, 3]}),
        },
    )

    rep = result.get_db_dict()
    insert_rep = results_db_service.insert_one(rep)
    assert insert_rep is not None
    return result


def check_generic_result_equal(generic_result, new_generic_obj):
    assert generic_result.flow_id == new_generic_obj.flow_id
    assert generic_result.inputs["input1"] == new_generic_obj.inputs["input1"]
    assert isinstance(new_generic_obj.inputs["input2"], np.ndarray)
    assert np.array_equal(
        generic_result.inputs["input2"], new_generic_obj.inputs["input2"]
    )
    assert new_generic_obj.outputs["output1"] == new_generic_obj.outputs["output1"]
    assert isinstance(new_generic_obj.outputs["output2"], pd.DataFrame)


class TestBSON:
    def test_numpy_query(self, results_db_service, generic_result):

        query = {
            "inputs.input2": generic_result.inputs["input2"],
            "flow_id": generic_result.flow_id,
        }
        query = get_bson_dict(query)
        selected = results_db_service.find(
            collection=generic_result.project_name, query=query
        )

        assert len(selected)

        # load types
        db_dict = load_db_dict(selected[0])

        assert isinstance(db_dict["outputs"]["output2"], pd.DataFrame)

    def test_pandas_query(self, results_db_service, generic_result):

        query = {"outputs.output2": generic_result.outputs["output2"]}
        query = get_bson_dict(query)
        selected = results_db_service.find(
            collection=generic_result.project_name, query=query
        )

        assert len(selected)

        # load types
        db_dict = load_db_dict(selected[0])

        assert isinstance(db_dict["outputs"]["output2"], pd.DataFrame)


@pytest.mark.parametrize(
    ("string", "result_class_target"),
    [
        ("lume_services.results.generic.Result", Result),
        ("lume_services.results.impact.ImpactResult", ImpactResult),
        pytest.param(
            "incorrect.import.string",
            Result,
            marks=pytest.mark.xfail(strict=True),
        ),
    ],
)
def test_get_result_from_string(string, result_class_target):
    result_type = get_result_from_string(string)
    assert result_type == result_class_target


class TestGenericResult:
    def test_create_generic_result_from_alias(self):
        Result(
            project_name="generic",
            flow_id="test_flow_id",
            inputs={"input1": 4, "input2": 3},
            outputs={"output1": 1},
        )

    def test_to_json(self, generic_result):
        generic_result.json()

    def test_from_json(self, generic_result):
        json_rep = generic_result.json()
        Result.parse_raw(json_rep)

    def test_from_dict(self, generic_result):
        dictionary = generic_result.dict(by_alias=True)
        Result(**dictionary)


class TestImpactResult:
    def test_to_json(self, impact_result):
        impact_result.json()

    def test_from_json(self, impact_result):
        json_rep = impact_result.json()
        ImpactResult.parse_raw(json_rep)

    def test_from_dict(self, impact_result):
        ImpactResult(**impact_result.get_db_dict())

    def test_load_image(self, impact_result, file_service):
        image = impact_result.plot_file.read(file_service=file_service)
        assert isinstance(image, (Image.Image,))


class TestMongodbResultsDBConfig:
    def test_construction(self):
        MongodbResultsDBConfig(
            database="results",
            host="localhost",
            username="user",
            port=3030,
            password="test",
        )

    def test_failed_construction(self):
        with pytest.raises(ValidationError):
            MongodbResultsDBConfig(
                database="results",
                host="localhost",
                username="user",
                port=3030,
            )


class TestMongodbResultsDB:
    def test_mongo_results_db_init(self, lume_services_settings):
        MongodbResultsDB(lume_services_settings.results_db)


class TestResultsDBService:
    @pytest.mark.skip("Indices not created at present.")
    def test_duplicate_generic_insert_fail(self, generic_result, results_db_service):
        # confirm duplicate raises error
        with pytest.raises(DuplicateKeyError):
            results_db_service.insert_one(generic_result.get_db_dict())

    @pytest.mark.skip("Indices not created at present.")
    def test_duplicate_impact_insert_fail(self, impact_result, results_db_service):
        # confirm duplicate raises error
        with pytest.raises(DuplicateKeyError):
            results_db_service.insert_one(impact_result.get_db_dict())

    def test_generic_result_query(self, results_db_service, generic_result):
        query = {
            "flow_id": generic_result.flow_id,
            "inputs": generic_result.inputs,
            "outputs": generic_result.outputs,
        }

        res = results_db_service.find(
            collection=generic_result.project_name,
            query=get_bson_dict(query),
        )

        new_generic_obj = Result(project_name=generic_result.project_name, **res[0])

        check_generic_result_equal(generic_result, new_generic_obj)

    def test_impact_result_query(self, results_db_service, impact_result):

        query = {
            "flow_id": impact_result.flow_id,
            "inputs": impact_result.inputs,
            "outputs": impact_result.outputs,
        }
        res = results_db_service.find(
            collection=impact_result.project_name,
            query=get_bson_dict(query),
        )

        new_impact_obj = ImpactResult(project_name=impact_result.project_name, **res[0])

        check_impact_result_equal(impact_result, new_impact_obj)

    def test_find_all(self, generic_result, results_db_service):
        res = results_db_service.find_all(collection=generic_result.project_name)
        assert isinstance(res, list)


class TestResultsInsertMethods:
    @pytest.fixture(scope="class", autouse=True)
    def generic_result2(self):
        result = Result(
            project_name="generic",
            flow_id="test_flow_id2",
            inputs={"input1": 2.0, "input2": np.array([1, 2, 9, 4, 5])},
            outputs={
                "output1": 2.0,
                "output2": pd.DataFrame({"x": [0, 1, 2], "y": [1, 2, 3]}),
            },
        )
        return result

    @pytest.fixture(scope="class", autouse=True)
    def impact_result2(self, project_name):
        result = ImpactResult(
            project_name="impact",
            flow_id="test_flow_impact_id2",
            inputs={
                "input1": 2.0,
                "input2": np.array([1, 2, 3, 4, 5]),
                "input3": "my_file.txt",
            },
            outputs={
                "output1": 2.0,
                "output2": np.array([1, 2, 9, 40, 5]),
                "output3": "my_file.txt",
            },
            plot_file=ImageFile(
                filename=SAMPLE_IMAGE_FILE, filesystem_identifier="local"
            ),
            archive=HDF5File(
                filename=SAMPLE_IMPACT_ARCHIVE, filesystem_identifier="local"
            ),
            pv_collection_isotime=datetime.now(),
            config={"config1": 1, "config2": 2},
        )
        return result

    @pytest.fixture(scope="class")
    def generic_result_insert_by_method(self, generic_result2, results_db_service):
        generic_result2.insert(results_db_service=results_db_service)

        # confirm duplicate raises error
        with pytest.raises(DuplicateKeyError):
            generic_result2.insert(results_db_service=results_db_service)

    @pytest.mark.usefixtures("generic_result_insert_by_method")
    def test_load_generic_result(self, generic_result2, results_db_service):
        new_generic_obj = Result.load_from_query(
            generic_result2.project_name,
            {
                "flow_id": generic_result2.flow_id,
                "inputs": generic_result2.inputs,
                "outputs": generic_result2.outputs,
            },
            results_db_service=results_db_service,
        )

        check_generic_result_equal(generic_result2, new_generic_obj)

    @pytest.fixture(scope="class")
    def impact_result_insert_by_method(self, impact_result2, results_db_service):
        impact_result2.insert(results_db_service=results_db_service)

        # confirm duplicate raises error
        with pytest.raises(DuplicateKeyError):
            impact_result2.insert(results_db_service=results_db_service)

    @pytest.mark.usefixtures("impact_result_insert_by_method")
    def test_load_impact_result(self, impact_result2, results_db_service):
        new_impact_obj = ImpactResult.load_from_query(
            impact_result2.project_name,
            {
                "flow_id": impact_result2.flow_id,
                "inputs": impact_result2.inputs,
                "outputs": impact_result2.outputs,
            },
            results_db_service=results_db_service,
        )
        check_impact_result_equal(impact_result2, new_impact_obj)
