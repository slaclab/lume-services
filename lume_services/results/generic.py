import json
from pydantic import field_validator, model_validator, ConfigDict, BaseModel, Field, validator
from datetime import datetime
from lume_services.services.results import ResultsDB
from lume_services.utils import fingerprint_dict
from typing import Any, ClassVar, List, Optional, Union, Dict
import numpy as np
import pandas as pd
import pickle

from dependency_injector.wiring import Provide, inject
from bson.objectid import ObjectId
from bson import Binary

from lume_services.config import Context
from lume_services.utils import JSON_ENCODERS
from lume_services.files import File, get_file_from_serializer_string

from prefect import context as prefect_context

import logging

logger = logging.getLogger(__name__)


def round_datetime_to_milliseconds(time: Union[datetime, str]) -> datetime:
    """Mongodb rounds datetime to milliseconds so round on assignment for
    consistency.

    """
    if isinstance(time, datetime):
        time = time.isoformat(timespec="milliseconds")
    return time


class Result(BaseModel):
    """Creates a data model for a result and generates a unique result hash."""

    project_name: str = Field(
        "local", alias="collection"
    )  # this will be the project_name for the scheduled flow

    # database id
    id: Optional[str] = Field(None, alias="_id", exclude=True)

    # db fields
    flow_id: str
    inputs: Dict[str, Union[float, str, np.ndarray, list, pd.DataFrame]]
    outputs: Dict[str, Union[float, str, np.ndarray, list, pd.DataFrame]]
    date_modified: datetime = datetime.utcnow()

    # set of establishes uniqueness
    unique_on: List[str] = Field(
        ["inputs", "outputs", "flow_id"], alias="index", exclude=True
    )

    # establishes uniqueness
    unique_hash: str

    # store result type
    result_type_string: str

    insert: ClassVar[Any]
    load_from_query: ClassVar[Any]

    # TODO[pydantic]: The following keys were removed: `json_encoders`.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
    model_config = ConfigDict(arbitrary_types_allowed=True, json_encoders=JSON_ENCODERS, populate_by_name=True, extra="forbid")

    _round_datetime_to_milliseconds = validator(
        "date_modified", allow_reuse=True, always=True, pre=True
    )(round_datetime_to_milliseconds)

    @field_validator("inputs", mode="before")
    @classmethod
    def validate_inputs(cls, v):
        return load_db_dict(v)

    @field_validator("outputs", mode="before")
    @classmethod
    def validate_outputs(cls, v):
        return load_db_dict(v)

    @model_validator(mode="before")
    @classmethod
    def validate_all(cls, values):
        unique_fields = cls.__fields__["unique_on"].default

        # If flow_id is not passed, check prefect context
        if not values.get("flow_id"):
            if not hasattr(prefect_context, "flow_id"):
                raise ValueError("No flow_id passed to result")

            values["flow_id"] = prefect_context.flow_id

        if not values.get("collection") and not values.get("project_name"):
            if not hasattr(prefect_context, "project_name"):
                logger.warning("No project_name passed to result")

            else:
                values["project_name"] = prefect_context.project_name

        # create index hash
        if not values.get("unique_hash"):

            for field in unique_fields:
                if not values.get(field):
                    raise ValueError("%s not provided.", field)

            values["unique_hash"] = fingerprint_dict(
                {index: values[index] for index in unique_fields}
            )

        if values.get("_id"):
            _id = values["_id"]
            if isinstance(_id, (ObjectId,)):
                values["_id"] = str(values["_id"])

        values["result_type_string"] = f"{cls.__module__}.{cls.__name__}"

        return values

    def get_unique_result_index(self) -> dict:
        return {field: getattr(self, field) for field in self.unique_on}

    @inject
    def insert(
        self, results_db_service: ResultsDB = Provide[Context.results_db_service]
    ):

        # must convert to jsonable dict
        rep = self.get_db_dict()
        return results_db_service.insert_one(rep)

    @classmethod
    @inject
    def load_from_query(
        cls,
        project_name: str,
        query: dict,
        results_db_service: ResultsDB = Provide[Context.results_db_service],
    ):
        query = get_bson_dict(query)
        res = results_db_service.find(collection=project_name, query=query)

        if len(res) == 0:
            raise ValueError("Provided query returned no results. %s", query)

        elif len(res) > 1:
            raise ValueError("Provided query returned multiple results. %s", query)

        values = load_db_dict(res[0])
        return cls(project_name=project_name, **values)

    def unique_rep(self) -> dict:
        """Get minimal representation needed to load result object from database."""

        return {
            "project_name": self.project_name,
            "result_type_string": self.result_type_string,
            "query": {"unique_hash": self.unique_hash},
        }

    def get_db_dict(self) -> dict:
        rep = self.dict(by_alias=True)
        return get_bson_dict(rep)


def get_bson_dict(dictionary: dict) -> dict:
    """Recursively converts numpy arrays inside a dictionary to bson encoded items and
    pandas dataframes to json reps.

    Args:
        dictionary (dict): Dictionary to load.

    Returns
        dict
    """

    def convert_values(dictionary):
        """Convert values to list so the dictionary can be inserted and loaded."""

        # convert numpy arrays to binary format
        dictionary = {
            key: Binary(pickle.dumps(value, protocol=2))
            if isinstance(value, (np.ndarray,))
            else value
            for key, value in dictionary.items()
        }

        # convert pandas array to json
        dictionary = {
            key: value.to_json() if isinstance(value, (pd.DataFrame,)) else value
            for key, value in dictionary.items()
        }

        # create file rep
        dictionary = {
            key: value.jsonable_dict() if isinstance(value, (File,)) else value
            for key, value in dictionary.items()
        }

        dictionary = {
            key: convert_values(value) if isinstance(value, (dict,)) else value
            for key, value in dictionary.items()
        }
        return dictionary

    return convert_values(dictionary)


def load_db_dict(dictionary: dict):
    """Loads representation of mongodb dictionary with appropriate python classes.
    Numpy arrays are loaded from binary objects and pandas dataframes from json blobs.

    Args:
        dictionary (dict): Dictionary to load.

    """

    def check_and_convert_json_str(string: str):
        try:

            loaded_ = json.loads(string)
            return pd.DataFrame(loaded_)

        except json.JSONDecodeError:
            return string

    def convert_values(dictionary):
        if "file_type_string" in dictionary:
            file_type = get_file_from_serializer_string(dictionary["file_type_string"])
            return file_type(**dictionary)

        # convert numpy arrays from binary format
        dictionary = {
            key: pickle.loads(value) if isinstance(value, (bytes,)) else value
            for key, value in dictionary.items()
        }

        # convert pandas array to json
        dictionary = {
            key: check_and_convert_json_str(value)
            if isinstance(value, (str,))
            else value
            for key, value in dictionary.items()
        }

        dictionary = {
            key: convert_values(value) if isinstance(value, (dict,)) else value
            for key, value in dictionary.items()
        }

        return dictionary

    return convert_values(dictionary)
