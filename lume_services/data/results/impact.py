from pydantic import Extra
from datetime import datetime

from typing import Optional

from lume_services.data.results.generic import GenericResult
from lume_services.utils import JSON_ENCODERS
from lume_services.data.files import HDF5File, ImageFile


class ImpactResult(GenericResult):
    """Extends GenericResult base and implements Impact specific attributes"""

    model_type: str = "Impact"
    plot_file: Optional[ImageFile]
    archive: HDF5File
    pv_collection_isotime: datetime
    config: dict

    class Config:
        allow_arbitrary_types = True
        json_encoders = JSON_ENCODERS
        extra = Extra.forbid
