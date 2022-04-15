import cloudpickle
import pytest

import prefect
from prefect.engine.result import Result, NoResultType
from prefect.engine.result.base import ResultNotImplementedError
from lume_services.scheduling.prefect.results.db import DBResult



"""
class TestInitialization:
    def test_result_does_not_require_a_value(self):
        assert Result().value is None

    def test_result_inits_with_value(self):
        r = Result(3)
        assert r.value == 3
        assert r.location is None

        s = Result(value=5)
        assert s.value == 5
        assert s.location is None
"""

def test_result_service_injection(test_generic_result_document, context):
    result = DBResult(value= test_generic_result_document, model_type="Generic")

    #check location is None
    assert result.location is None


def test_generic_result(results_service, test_generic_result_document):
    result = DBResult(value= test_generic_result_document, model_type="Generic", results_service=results_service)

    #check location is None
    assert result.location is None


def test_generic_everything_is_pickleable_after_init(results_service, test_generic_result_document):
    result = DBResult(value= test_generic_result_document, model_type="Generic", results_service=results_service)

    assert cloudpickle.loads(cloudpickle.dumps(result)) == result


def test_write_generic_result(results_service, test_generic_result_document):
    result = DBResult(model_type="Generic", results_service=results_service)
    result.write(test_generic_result_document)
    return result

def test_write_impact_result(results_service, test_impact_result_document):
    result = DBResult(value= test_impact_result_document, model_type="Impact", results_service=results_service)
    result.write(test_impact_result_document)
    return result
