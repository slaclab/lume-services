from .generic import Result
from .impact import ImpactResult
from typing import Dict

import logging

from lume_services.utils import fingerprint_dict, get_callable_from_string

logger = logging.getLogger(__name__)

# create map of type import path to type
_ResultTypes = {
    f"{Result.__module__}:{Result.__name__}": Result,
    f"{ImpactResult.__module__}:{ImpactResult.__name__}": ImpactResult,
}


def get_result_from_string(result_type_string: str) -> Result:
    """Returns a LUME-model result type from a string import path.

    Args:
        result_type_string (str): Full import path of result type class.

    """

    result_class = get_callable_from_string(result_type_string)

    if not issubclass(result_class, Result):
        raise ValueError(
            "Result type is not a subclass of lume_services.results.generic.Result. %s",
            result_class.__name__,
        )

    else:
        return result_class


def get_result_types() -> Dict[str, Result]:
    """Get mapping of result import strings to LUME-services results objects.

    Returns:
        Dict[str, Result]: Mapping of result import strings to LUME-services results
            objects.

    """
    return _ResultTypes


def get_unique_hash(result_rep) -> str:
    """Get a unique hash identifier of the result using the unique result fields.

    Args:
        result_rep (dict): Dictionary representation of the result.

    """
    result_type = get_result_from_string(result_rep["result_type_string"])

    unique_fields = result_type.__fields__["unique_on"].default

    return fingerprint_dict(
        {index: result_rep["query"][index] for index in unique_fields}
    )
