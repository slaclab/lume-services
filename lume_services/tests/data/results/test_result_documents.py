from lume_services.data.results.db.mongodb.models.impact import ImpactResultDocument
from lume_services.data.results.db.mongodb.document import GenericResultDocument
from datetime import datetime
import pytest


@pytest.mark.run(order=1)
def test_construct_result_document(test_generic_result_document):
    result_doc_instance = GenericResultDocument(**test_generic_result_document)


@pytest.mark.run(order=1)
def test_construct_impact_result_document(test_impact_result_document, test_generic_result_document):

    # check missing fields
    missing_field_doc = ImpactResultDocument(**test_generic_result_document)
    validation_error = ImpactResultDocument.get_validation_error()
    with pytest.raises(validation_error):
        missing_field_doc.validate()

  #  del missing_field_doc
    result_doc_instance = ImpactResultDocument(**test_impact_result_document)
  #  del result_doc_instance

def test_distinct_collection(test_impact_result_document, test_generic_result_document):

    # confirm using distinct names for collection
    result_doc_instance = GenericResultDocument(**test_generic_result_document)
    impact_doc_instance = ImpactResultDocument(**test_impact_result_document)
    
    assert result_doc_instance._get_collection_name() != impact_doc_instance._get_collection_name()
