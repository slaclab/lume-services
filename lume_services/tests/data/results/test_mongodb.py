import pytest


@pytest.fixture(scope="module", autouse=True)
def test_result_doc_insert(test_generic_result_document, results_db_service):

    test_result_doc_insert = results_db_service.store("Generic", **test_generic_result_document)

    return test_result_doc_insert


def test_result_doc_load(results_db_service, test_result_doc_insert):

    res = results_db_service.find("Generic", query={"id":test_result_doc_insert})

    assert len(res)
    assert res[0].id == test_result_doc_insert


@pytest.fixture(scope="module", autouse=True)
def test_impact_doc_insert(test_impact_result_document, results_db_service):
    insert_type = "Impact"

    res = results_db_service.store(insert_type, **test_impact_result_document)

    return res


def test_impact_doc_load(results_db_service, test_impact_doc_insert):
    res = results_db_service.find("Impact", query={"id":test_impact_doc_insert})

    assert len(res) >= 0

    assert res[0].id == test_impact_doc_insert

""""
def test_undefined_model_name():
    ...

def test_extra_field
"""