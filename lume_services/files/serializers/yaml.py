from lume.serializers.base import SerializerBase
from typing import List
import yaml
import logging

logger = logging.getLogger(__name__)


class YAMLSerializer(SerializerBase):
    """Serializer sublass handling YAML files."""

    def serialize(self, filename: str, object: List[dict]) -> None:
        """Serialize an object to a YAML.


        Args:
            filename (str): Name of file to write.
            object (List[dict]): Object to serialize.

        """

        with open(filename, "w") as f:
            yaml.dump(object, f)

    @classmethod
    def deserialize(cls, filename: str) -> List[dict]:
        """Deserializes a given YAML file.

        Args:
            filename (str): Name of file to deserialize.

        Returns:
            List[dict]: Loaded YAML representation.

        """
        yaml_rep = None

        with open(filename, "r") as f:

            try:
                yaml_rep = yaml.safe_load(f)

            except yaml.YAMLError as exc:
                logger.exception(exc)

        return yaml_rep
