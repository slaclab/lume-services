from pydantic import BaseSettings
import json
import logging 
import hashlib

logger = logging.getLogger(__name__)


def filter_keys_in_settings(dictionary: dict, settings_obj: BaseSettings):
    """Utility function for checking the membership of dictionary keys in a settings class definition.
    
    """
    not_in_settings = [key for key in dictionary.keys() if key not in settings_obj.attributes]
    in_settings = [key for key in dictionary.keys() if key not in settings_obj.attributes]

    if len(not_in_settings):
        logger.warning("Key %s not found in settings. Allowed keys are for %s are %s", ",".join(not_in_settings), 
        settings_obj.class_name, 
        ",".join(settings_obj.attributes))

    return {key: value for key, value in dictionary.items() if key in in_settings}


def fingerprint_dict(dictionary: dict):

    hasher = hashlib.md5()
    hasher.update(
        json.dumps(dictionary).encode("utf-8")
    )
    return hasher.hexdigest()


def flatten_dict(d):
    def expand(key, value):
        if isinstance(value, dict):
            return [(k, v) for k, v in flatten_dict(value).items()]
        else:
            return [(key, value)]

    items = [item for k, v in d.items() for item in expand(k, v)]

    return dict(items)