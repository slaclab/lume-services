from datetime import datetime

from typing import Optional

from pydantic import Field
from lume_services.results.generic import Result
from lume_services.files import HDF5File, ImageFile


class ImpactResult(Result):
    """Extends Result base and implements Impact specific attributes"""

    model_type: str = Field("Impact", alias="collection")
    plot_file: Optional[ImageFile]
    archive: HDF5File
    pv_collection_isotime: datetime
    config: dict
