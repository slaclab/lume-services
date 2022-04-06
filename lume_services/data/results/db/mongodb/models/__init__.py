from enum import Enum
from typing import Literal

from lume_services.data.results.db.mongodb.models.impact import ImpactResultDocument
from lume_services.data.results.db.mongodb.document import ResultDocument


class ModelDocs(Enum):
    Generic = ResultDocument
    Impact = ImpactResultDocument
