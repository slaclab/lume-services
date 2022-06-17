from pydantic import BaseModel, root_validator, Field
from datetime import datetime
from lume_services.utils import fingerprint_dict
from typing import List


class GenericResult(BaseModel):
    """Creates a data model for a result and generates a unique result hash."""

    # points to field that establishes uniqueness
    target_field: str = Field(["unique_result_hash"], const=True)
    collection: str

    # db fields
    flow_id: str
    inputs: dict
    outputs: dict

    # establishes uniqueness
    index_fields: List[str] = Field(["inputs", "outputs", "flow_id"], const=True)

    date_modified: datetime = datetime.utcnow()
    meta: dict = {"ordering": ["-date_modified"]}

    # Used for identifying index
    unique_result_hash: str

    @root_validator(pre=True)
    def validate_all(cls, values):
        index_fields = cls.__fields__["index_fields"].default

        # create index hash
        if not values.get("unique_result_hash"):

            for field in index_fields:
                if not values.get(field):
                    raise ValueError("%s not provided.", field)

            values["unique_result_hash"] = fingerprint_dict(
                {index: values[index] for index in index_fields}
            )

        return values

    @root_validator(pre=False)
    def populate_meta(cls, values):
        values["meta"]["indexes"] = [
            # enforce uniqueness
            {
                "fields": values[
                    "index_fields"
                ],  # may need to account for _ in field name with - preceedng
                "unique": True,
                "name": "unique_result",
            },
        ]

        values["meta"]["collection"] = values["collection"]

        return values

    def get_unique_result_index(self) -> dict:
        return {field: getattr(self, field) for field in self.index_fields}
