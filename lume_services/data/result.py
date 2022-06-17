from lume_services.data.results import GenericResult, ImpactResult

# create map of type import path to type
_ResultTypeStringMap = {
    f"{GenericResult.__module__}:{GenericResult.__name__}": GenericResult,
    f"{ImpactResult.__module__}:{ImpactResult.__name__}": ImpactResult,
}


def get_result_from_string(result_type_string: str):

    if not _ResultTypeStringMap.get(result_type_string):
        raise ValueError(
            "String not in result types. %s, %s",
            result_type_string,
            list(_ResultTypeStringMap.keys()),
        )

    else:
        return _ResultTypeStringMap.get(result_type_string)
