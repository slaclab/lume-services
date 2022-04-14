from attr import field
from mongoengine import Document
from mongoengine import signals
from mongoengine.fields import StringField, DateTimeField, DictField
from datetime import datetime
from mongoengine.errors import ValidationError

from lume_services.utils import fingerprint_dict


class ResultDocument(Document):
    """Abstract base Document from which other result docs will inherit

    It may be necessary to overwrite the index specified here in subclasses. 
    
    """
    flow_id = StringField(max_length=200, required=True)
    inputs = DictField(required=True)
    outputs = DictField(required=True)
    date_modified = DateTimeField(default=datetime.utcnow)

    # Used for identifying index
    unique_result_hash = StringField(default=None)

    meta = {'abstract': True,
    'indexes': [
            # enforce uniqueness
            {'fields': ['inputs', 'outputs', '-flow_id'], 'unique': True, 'name': "unique_result"}, 

           ],
    'ordering': ['-date_modified'],
        }

    @staticmethod
    def get_validation_error():
        return ValidationError

    def get_pk_id(self):
        pk_id_field = self._meta.get("id_field")
        return getattr(self, pk_id_field)

    @classmethod
    def get_unique_result_index_fields(cls):
        index_specs = cls._meta.get("index_specs")

        for index in index_specs:
            if index["name"] == cls.unique_result_idx:
                return [field[0] for field in index["fields"]]

        raise ValidationError(f"Unique result index {cls.unique_result_idx} not found.")

    def get_unique_result_index(self):
        index_fields = self.get_unique_result_index_fields()
        return {field: getattr(self, field) for field in index_fields}

    @classmethod
    def post_init(cls, sender, document, **kwargs):
        document.unique_result_hash = fingerprint_dict(
                {
                    "inputs": document.inputs,
                    "outputs": document.outputs,
                    "flow_id": document.flow_id
                }
            )

class GenericResultDocument(ResultDocument):

    meta = {"collection": "Generic"}

signals.post_init.connect(ResultDocument.post_init, sender=GenericResultDocument)
