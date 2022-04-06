from mongoengine import Document
from mongoengine.fields import StringField, DateTimeField, DictField
from datetime import datetime

class ResultDocument(Document):
    flow_id = StringField(max_length=200, required=True)
    inputs = DictField(required=True)
    outputs = DictField(required=True)
    date_modified = DateTimeField(default=datetime.utcnow)

    meta = {'allow_inheritance': True,
    'indexes': [
            {'fields': ['inputs', 'outputs', '-flow_id'], 'unique': True}, # use compound index
           ],
    'ordering': ['-date_modified']
        }
