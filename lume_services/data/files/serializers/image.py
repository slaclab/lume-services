from lume.serializers.base import SerializerBase
from PIL import Image


class ImageSerializer(SerializerBase):
    """Pillow image serializer."""

    def serialize(self, filename, image: Image):
        image.save(filename)

    @classmethod
    def deserialize(cls, filename) -> Image:

        return Image.open(filename)
