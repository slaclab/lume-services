import cloudpickle

from lume_services.scheduling.prefect.results.db import DBResult


def test_result_service_injection(test_generic_result_document, context):
    result = DBResult(value=test_generic_result_document, model_type="Generic")

    # check location is None
    assert result.location is None


def test_generic_result(results_service, test_generic_result_document):
    result = DBResult(
        value=test_generic_result_document,
        model_type="Generic",
        results_service=results_service,
    )

    # check location is None
    assert result.location is None


def test_generic_everything_is_pickleable_after_init(
    results_service, test_generic_result_document
):
    result = DBResult(
        value=test_generic_result_document,
        model_type="Generic",
        results_service=results_service,
    )

    assert cloudpickle.loads(cloudpickle.dumps(result)) == result


def test_write_generic_result(results_service, test_generic_result_document):
    result = DBResult(model_type="Generic", results_service=results_service)
    result.write(test_generic_result_document)
    return result


def test_write_impact_result(results_service, test_impact_result_document):
    result = DBResult(
        value=test_impact_result_document,
        model_type="Impact",
        results_service=results_service,
    )
    result.write(test_impact_result_document)
    return result
