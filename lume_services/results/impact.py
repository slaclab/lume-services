from datetime import datetime

from typing import Optional

from pydantic import Field, validator
from lume_services.results.generic import Result
from lume_services.files import HDF5File, ImageFile


class ImpactResult(Result):
    """Extends Result base and implements Impact specific attributes"""

    model_type: str = Field("Impact", alias="collection")
    plot_file: Optional[ImageFile]
    archive: HDF5File
    pv_collection_isotime: datetime
    config: dict

    @validator("plot_file", pre=True)
    def validate_plot_file(cls, v):

        # if the plot file isinstance of dictionary, load file type
        if isinstance(v, dict):
            return ImageFile(**v)

        return v

    @validator("archive", pre=True)
    def validate_archive_file(cls, v):

        # if the plot file isinstance of dictionary, load file type
        if isinstance(v, dict):
            return HDF5File(**v)

        return v
