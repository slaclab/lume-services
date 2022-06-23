import json
from pydantic import BaseModel, root_validator, Field, Extra
from datetime import datetime
from lume_services.services.data.results import ResultsDB
from lume_services.utils import fingerprint_dict
from typing import List
from dependency_injector.wiring import Provide

from lume_services.context import Context
from lume_services.utils import JSON_ENCODERS


class GenericResult(BaseModel):
    """Creates a data model for a result and generates a unique result hash."""

    model_type: str = Field("generic", alias="collection")
    # id: Optional[ObjectId]

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

        values["result_type_string"] = f"{cls.__module__}:{cls.__name__}"

        return values

    def get_unique_result_index(self) -> dict:
        return {field: getattr(self, field) for field in self.unique_on}

    def insert(
        self, results_db_service: ResultsDB = Provide[Context.results_db_service]
    ):

        # must convert to jsonable dict
        rep = self.jsonable_dict()
        results_db_service.insert_one(rep)

    @classmethod
    def load_result_from_query(
        cls,
        query,
        results_db_service: ResultsDB = Provide[Context.results_db_service],
    ):
        res = results_db_service.find(collection=cls.model_type, query=query)
        return cls(**res)

    def load_result(
        self,
        results_db_service: ResultsDB = Provide[Context.results_db_service],
    ):
        res = results_db_service.find(
            collection=self.model_type, query={"unique_hash": self.unique_hash}
        )
        return res

    def jsonable_dict(self):
        return json.loads(self.json(by_alias=True))
