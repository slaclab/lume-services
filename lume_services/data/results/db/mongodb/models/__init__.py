from enum import Enum
from typing import Literal

from lume_services.data.results.db.models.impact import ImpactResultDocument
from lume_services.data.results.db.document import ResultDocument


class ModelDocs(Enum):
    Generic = ResultDocument
    Impact = ImpactResultDocument
