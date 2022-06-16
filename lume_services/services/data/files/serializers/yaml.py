from lume.serializers.base import SerializerBase
from typing import List
import yaml


class YAMLSerializer(SerializerBase):
    def serialize(self, filename, object: List[dict]) -> None:

        with open(filename, "w") as f:
            yaml.dump(object, f)

    @classmethod
    def deserialize(cls, filename: str) -> List[dict]:
        yaml_rep = None

        with open(filename, "r") as f:

            try:
                yaml_rep = yaml.safe_load(f)

            except yaml.YAMLError as exc:
                print(exc)

        return yaml_rep
