from datetime import datetime

from typing import Optional

from pydantic import Field, validator
from lume_services.results.generic import Result
from lume_services.files import HDF5File, ImageFile, get_file_from_serializer_string


class ImpactResult(Result):
    """Extends Result base and implements Impact specific attributes"""

    model_type: str = Field("Impact", alias="collection")
    plot_file: Optional[ImageFile]
    archive: HDF5File
    pv_collection_isotime: datetime
    config: dict

    @validator("plot_file", "archive", pre=True)
    def validate_file(cls, v):

        # if the plot file isinstance of dictionary, load file using file_type_string
        if isinstance(v, dict):
            file_type = get_file_from_serializer_string(v["file_type_string"])
            return file_type(**v)

        return v
