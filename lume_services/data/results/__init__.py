from .generic import GenericResult
from .impact import ImpactResult
from typing import List, Dict

import logging

logger = logging.getLogger(__name__)

# create map of type import path to type
_ResultTypes = {
    f"{GenericResult.__module__}:{GenericResult.__name__}": GenericResult,
    f"{ImpactResult.__module__}:{ImpactResult.__name__}": ImpactResult,
}


def get_result_from_string(result_type_string: str):

    if not _ResultTypes.get(result_type_string):
        raise ValueError(
            "String not in result types. %s, %s",
            result_type_string,
            list(_ResultTypes.keys()),
        )

    else:
        return _ResultTypes.get(result_type_string)


def get_result_types():
    return _ResultTypes


def get_collections() -> Dict[str, List[str]]:
    """Utility function for returning result collection info.

    Returns:
        dict: Dictionary mapping collection name to unique index.

    """
    collection_rep = {}

    for res_type in _ResultTypes.values():
        collection = res_type.__fields__["model_type"].default
        collection_index = res_type.__fields__["unique_on"].default
        collection_rep[collection] = collection_index

    return collection_rep
