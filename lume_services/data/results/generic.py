import json
from pydantic import BaseModel, root_validator, Field, Extra
from datetime import datetime
from lume_services.services.data.results import ResultsDB
from lume_services.utils import fingerprint_dict
from typing import List, Optional
from dependency_injector.wiring import Provide, inject
from bson.objectid import ObjectId

from lume_services.config import Context
from lume_services.utils import JSON_ENCODERS

from prefect import context


class Result(BaseModel):
    """Creates a data model for a result and generates a unique result hash."""

    model_type: str = Field("generic", alias="collection")

    # database id
    id: Optional[str] = Field(alias="_id", exclude=True)

    # db fields
    flow_id: str
    inputs: dict
    outputs: dict
    date_modified: datetime = datetime.utcnow()

    # set of establishes uniqueness
    unique_on: List[str] = Field(
        ["inputs", "outputs", "flow_id"], alias="index", exclude=True
    )

    # establishes uniqueness
    unique_hash: str

    # store result type
    result_type_string: str

    class Config:
        allow_arbitrary_types = True
        json_encoders = JSON_ENCODERS
        allow_population_by_field_name = True
        extra = Extra.forbid

    @root_validator(pre=True)
    def validate_all(cls, values):
        unique_fields = cls.__fields__["unique_on"].default

        # create index hash
        if not values.get("unique_hash"):

            for field in unique_fields:
                if not values.get(field):
                    raise ValueError("%s not provided.", field)

            values["unique_hash"] = fingerprint_dict(
                {index: values[index] for index in unique_fields}
            )

        if values.get("_id"):
            id = values["_id"]
            if isinstance(id, (ObjectId,)):
                values["_id"] = str(values["_id"])

        # If flow_id is not passed, check prefect context
        if not values.get("flow_id"):
            values["flow_id"] = context.flow_id

        values["result_type_string"] = f"{cls.__module__}:{cls.__name__}"

        return values

    def get_unique_result_index(self) -> dict:
        return {field: getattr(self, field) for field in self.unique_on}

    @inject
    def insert(
        self, results_db_service: ResultsDB = Provide[Context.results_db_service]
    ):

        # must convert to jsonable dict
        rep = self.jsonable_dict()
        return results_db_service.insert_one(rep)

    @classmethod
    @inject
    def load_from_query(
        cls,
        query,
        results_db_service: ResultsDB = Provide[Context.results_db_service],
    ):
        res = results_db_service.find(
            collection=cls.__fields__["model_type"].default, query=query
        )

        if len(res) == 0:
            raise ValueError("Provided query returned no results. %s", query)

        elif len(res) > 1:
            raise ValueError("Provided query returned multiple results. %s", query)

        return cls(**res[0])

    def jsonable_dict(self) -> dict:
        return json.loads(self.json(by_alias=True))

    def unique_rep(self) -> dict:
        """Get minimal representation needed to load result object from database."""
        return {
            "result_type_string": self.result_type_string,
            "query": self.get_unique_result_index(),
        }
