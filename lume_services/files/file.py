import logging
import json
from dependency_injector.wiring import Provide, inject

from typing import Optional, Generic, Any, ClassVar
from pydantic import model_validator, BaseModel, ConfigDict, Field

import copy

from lume_services.config import Context
from lume_services.services.files import FileService
from lume_services.files.serializers import (
    TextSerializer,
    ImageSerializer,
    YAMLSerializer,
)
from lume_services.utils import ObjLoader, ObjType, JSON_ENCODERS

from lume.serializers.hdf5 import HDF5Serializer

logger = logging.getLogger(__name__)


class File(
    BaseModel, Generic[ObjType]
):
    filename: str
    file_type_string: str
    filesystem_identifier: str = "local"

    # Object to-be-serialized/result of deserialization
    obj: Any = Field(None, exclude=True)

    loader: Optional[ObjLoader[ObjType]] = Field(exclude=True)
    serializer: ObjType = Field(exclude=True)

    load: bool = Field(False, exclude=True)

    write: ClassVar[Any]
    read: ClassVar[Any]
    load_file: ClassVar[Any]

    model_config = ConfigDict(arbitrary_types_allowed=True, json_encoders=JSON_ENCODERS)

    @model_validator(mode="before")
    @classmethod
    def validate_all(cls, values):
        serializer_type = cls.__fields__["serializer"].type_

        # Compose loader utility
        if values.get("loader") is not None:
            loader_values = values["loader"]
            loader = ObjLoader[serializer_type](**loader_values)

        else:
            # maintain reference to original object
            loader_values = copy.copy(values)

            # if serializer in values, need to remove
            if "serializer" in loader_values:
                loader_values.pop("serializer")

            # if serializer_type in values, need to remove
            if "serializer_type" in loader_values:
                loader_values.pop("serializer_type")

            # if serializer_type in values, need to remove
            if "filename" in loader_values:
                loader_values.pop("filename")

            # if filesystem_identifier in values, need to remove
            if "filesystem_identifier" in loader_values:
                loader_values.pop("filesystem_identifier")

            # if filesystem_identifier in values, need to remove
            if "file_type_string" in loader_values:
                loader_values.pop("file_type_string")

            # if obj in values, need to remove
            if "obj" in loader_values:
                loader_values.pop("obj")

            loader = ObjLoader[serializer_type](**loader_values)

        values["serializer_type"] = serializer_type
        values["loader"] = loader
        values["serializer"] = loader.load()

        values["file_type_string"] = f"{cls.__module__}:{cls.__name__}"

        # update the class json encoders. Will only execute on initial type construction
        if serializer_type not in cls.__config__.json_encoders:
            cls.__config__.json_encoders[
                serializer_type
            ] = cls.__config__.json_encoders.pop(ObjType)

        return values

    @inject
    def write(
        self,
        obj=None,
        file_service: FileService = Provide[Context.file_service],
        create_dir=False,
    ):
        if not obj:
            if not self.obj:
                raise ValueError("Must provide object to write.")

            file_service.write(
                self.filesystem_identifier,
                self.filename,
                self.obj,
                self.serializer,
                create_dir=create_dir,
            )
        else:
            self.obj = obj
            file_service.write(
                self.filesystem_identifier,
                self.filename,
                obj,
                self.serializer,
                create_dir=create_dir,
            )

    @inject
    def read(self, file_service: FileService = Provide[Context.file_service]):
        return file_service.read(
            self.filesystem_identifier,
            self.filename,
            self.serializer,
        )

    @inject
    def load_file(
        self, file_service: FileService = Provide[Context.file_service]
    ) -> None:
        """Load file object from instantiated File."""
        self.obj = self.read(file_service=file_service)

    def jsonable_dict(self) -> dict:
        return json.loads(self.json(by_alias=True))


TextFile = File[TextSerializer]
HDF5File = File[HDF5Serializer]
ImageFile = File[ImageSerializer]
YAMLFile = File[YAMLSerializer]
