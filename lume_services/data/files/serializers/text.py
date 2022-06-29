from lume.serializers.base import SerializerBase


class TextSerializer(SerializerBase):
    def serialize(self, filename, text):

        with open(filename, "w") as f:
            f.write(text)

    @classmethod
    def deserialize(cls, filename):

        text = ""

        with open(filename, "r") as f:
            text = f.read()

        return text
