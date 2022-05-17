from lume_services.data.results.db.mongodb.models.impact import ImpactResultDocument
from lume_services.data.results.db.mongodb.document import GenericResultDocument
import pytest


def test_construct_result_document(test_generic_result_document):
    result_doc_instance = GenericResultDocument(**test_generic_result_document)

    assert result_doc_instance.unique_result_hash is not None


def test_construct_impact_result_document(
    test_impact_result_document, test_generic_result_document
):

    # check missing fields
    missing_field_doc = ImpactResultDocument(**test_generic_result_document)
    validation_error = ImpactResultDocument.get_validation_error()
    with pytest.raises(validation_error):
        missing_field_doc.validate()

    result_doc_instance = ImpactResultDocument(**test_impact_result_document)

    assert result_doc_instance.unique_result_hash is not None


def test_distinct_collection(test_impact_result_document, test_generic_result_document):

    # confirm using distinct names for collection
    result_doc_instance = GenericResultDocument(**test_generic_result_document)
    impact_doc_instance = ImpactResultDocument(**test_impact_result_document)

    result_doc_collection = result_doc_instance._get_collection_name()
    impact_doc_collection = impact_doc_instance._get_collection_name()

    assert result_doc_collection != impact_doc_collection
