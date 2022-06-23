from datetime import datetime

from typing import Optional

from pydantic import Field
from lume_services.data.results.generic import GenericResult
from lume_services.data.files import HDF5File, ImageFile


class ImpactResult(GenericResult):
    """Extends GenericResult base and implements Impact specific attributes"""

    model_type: str = Field("Impact", alias="collection")
    plot_file: Optional[ImageFile]
    archive: HDF5File
    pv_collection_isotime: datetime
    config: dict
