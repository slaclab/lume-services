from mongoengine import Document
from mongoengine.fields import StringField, DateTimeField, DictField
from datetime import datetime
from mongoengine.errors import ValidationError


class ResultDocument(Document):
    """Abstract base Document from which other result docs will inherit
    
    """
    flow_id = StringField(max_length=200, required=True)
    inputs = DictField(required=True)
    outputs = DictField(required=True)
    date_modified = DateTimeField(default=datetime.utcnow)

    meta = {'abstract': True,
    'indexes': [
            {'fields': ['inputs', 'outputs', '-flow_id'], 'unique': True}, # use compound index
           ],
    'ordering': ['-date_modified'],
        }

    @staticmethod
    def get_validation_error():
        return ValidationError

    def get_pk_id(self):
        pk_id_field = self._meta.get("id_field")
        return getattr(self, pk_id_field)


class GenericResultDocument(ResultDocument):

    meta = {"collection": "Generic"}