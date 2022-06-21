from pydantic import BaseModel, root_validator, Field
from datetime import datetime
from lume_services.services.data.results import ResultsDBService
from lume_services.utils import fingerprint_dict
from typing import List
from dependency_injector.wiring import Provide

from lume_services.context import Context


class GenericResult(BaseModel):
    """Creates a data model for a result and generates a unique result hash."""

    model_type: str = Field("generic", alias="collection", exclude=True)
    # id: Optional[ObjectId]

    # db fields
    flow_id: str
    inputs: dict
    outputs: dict
    date_modified: datetime = datetime.utcnow()

    # set of establishes uniqueness
    unique_on: List[str] = Field(
        ["inputs", "outputs", "flow_id"], const=True, alias="index", exclude=True
    )

    # establishes uniqueness
    unique_hash: str

    # store result type
    result_type: type

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

        values["result_type"] = cls

        return values

    def get_unique_result_index(self) -> dict:
        return {field: getattr(self, field) for field in self.unique_on}

    def insert(
        self, results_db_service: ResultsDBService = Provide[Context.results_db_service]
    ):
        rep = self.dict()
        results_db_service.insert_one(item=rep, collection=self.collection)

    @classmethod
    def load_result(
        cls,
        query,
        results_db_service: ResultsDBService = Provide[Context.results_db_service],
    ):
        res = results_db_service.find(collection=cls.collection, query=query)
        return cls(**res)
