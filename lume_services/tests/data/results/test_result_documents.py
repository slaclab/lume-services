from lume_services.data.results.db.models.impact import ImpactResultDocument
from lume_services.data.results.db.document import ResultDocument
from datetime import datetime

from mongoengine import ValidationError
import pytest


@pytest.fixture(autouse=True)
def test_result_document():
    return  {
        "flow_id": "test_flow_id",
        "inputs": {
            "input1": 2.0,
            "input2": [1,2,3,4,5],
            "input3": "my_file.txt"
        },
        "outputs": {
            "output1": 2.0,
            "output2": [1,2,3,4,5],
            "ouptut3": "my_file.txt"
        },
    }


@pytest.fixture(autouse=True)
def test_impact_document():
    return  {
        "flow_id": "test_flow_id",
        "inputs": {
            "input1": 2.0,
            "input2": [1,2,3,4,5],
            "input3": "my_file.txt"
        },
        "outputs": {
            "output1": 2.0,
            "output2": [1,2,3,4,5],
            "ouptut3": "my_file.txt"
        },
        "plot_file": "my_plot_file.txt",
        "archive": "archive_file.txt",
        "pv_collection_isotime": datetime.now(),
        "config": {
            "config1": 1,
            "config2": 2
        }
    }


def test_construct_result_document(test_result_document):
    result_doc_instance = ResultDocument(**test_result_document)


def test_construct_impact_result_document(test_impact_document, test_result_document):
    result_doc_instance = ImpactResultDocument(**test_impact_document)

    # check missing fields
    with pytest.raises(ValidationError):
        missing_field_doc = ImpactResultDocument(**test_result_document)
        missing_field_doc.validate()
