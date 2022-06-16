import logging
from dependency_injector.wiring import Provide

from typing import Optional, Generic
from pydantic import root_validator, Field
from pydantic.generics import GenericModel

import copy

from lume_services.context import Context
from lume_services.services.data.files import FileService
from lume_services.data.files.serializers import TextSerializer
from lume_services.utils import ObjLoader, ObjType, JSON_ENCODERS

from lume.serializers.hdf5 import HDF5Serializer

logger = logging.getLogger(__name__)


class File(
    GenericModel,
    Generic[ObjType],
    arbitrary_types_allowed=True,
    json_encoders=JSON_ENCODERS,
):
    filename: str
    loader: Optional[ObjLoader[ObjType]]
    serializer: ObjType = Field(exclude=True)
    file_system_identifier: str = "local"
    serializer_type: type

    @root_validator(pre=True)
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

            # if file_system_identifier in values, need to remove
            if "file_system_identifier" in loader_values:
                loader_values.pop("file_system_identifier")

            loader = ObjLoader[serializer_type](**loader_values)

        values["serializer_type"] = serializer_type
        values["loader"] = loader
        values["serializer"] = loader.load()

        # update the class json encoders. Will only execute on initial type construction
        if serializer_type not in cls.__config__.json_encoders:
            cls.__config__.json_encoders[
                serializer_type
            ] = cls.__config__.json_encoders.pop(ObjType)

        return values

    def write(
        self,
        obj,
        file_service: FileService = Provide[Context.file_service],
        create_dir=False,
    ):
        file_service.write(
            self.file_system_identifier,
            self.filename,
            obj,
            self.serializer,
            create_dir=create_dir,
        )

    def read(self, file_service: FileService = Provide[Context.file_service]):
        return file_service.read(
            self.file_system_identifier,
            self.filename,
            self.serializer,
        )


TextFile = File[TextSerializer]
HDF5File = File[HDF5Serializer]

# create map of type import path to type
_FileSerializerTypeStringMap = {
    f"{TextSerializer.__module__}:{TextSerializer.__name__}": TextFile,
    f"{HDF5Serializer.__module__}:{HDF5Serializer.__name__}": HDF5File,
}


def get_file_from_serializer_string(serializer_type_string=str):

    if not _FileSerializerTypeStringMap.get(serializer_type_string):
        raise ValueError(
            "Serializer string not in file types. %s, %s",
            serializer_type_string,
            _FileSerializerTypeStringMap.keys(),
        )

    else:
        return _FileSerializerTypeStringMap.get(serializer_type_string)