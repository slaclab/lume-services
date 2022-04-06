from lume_services.data.results.db.mongodb.document import ResultDocument
from mongoengine.fields import StringField, DateTimeField, DictField


class ImpactResultDocument(ResultDocument):
    plot_file = StringField(max_length=200, required=True)
    archive = StringField(max_length=200, required=True)
    pv_collection_isotime = DateTimeField(required=True)
    config = DictField(required=True)

    meta = {'collection': 'Impact'}

