from enum import Enum
from typing import Literal

from lume_services.data.results.db.mongodb.models.impact import ImpactResultDocument
from lume_services.data.results.db.mongodb.document import GenericResultDocument


class ModelDocs(Enum):
    Generic = GenericResultDocument
    Impact = ImpactResultDocument
