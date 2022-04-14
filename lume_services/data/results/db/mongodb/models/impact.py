from lume_services.data.results.db.mongodb.document import ResultDocument
from mongoengine.fields import StringField, DateTimeField, DictField
from mongoengine import signals


class ImpactResultDocument(ResultDocument):
    """Extends ResultDocument base and implements Impact specific collection"""

    plot_file = StringField(max_length=200, required=True)
    archive = StringField(max_length=200, required=True)
    pv_collection_isotime = DateTimeField(required=True)
    config = DictField(required=True)

    meta = {
        "collection": "Impact",
        "indexes": [
            {
                "fields": ["inputs", "outputs", "-flow_id"],
                "unique": True,
            },  # use compound index
        ],
    }


signals.post_init.connect(ResultDocument.post_init, sender=ImpactResultDocument)
