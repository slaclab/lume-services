from enum import Enum

from lume_services.data.results.db.mongodb.models.impact import ImpactResultDocument
from lume_services.data.results.db.mongodb.document import GenericResultDocument


ModelDocs = {
    "Generic": GenericResultDocument,
    "Impact": ImpactResultDocument
}