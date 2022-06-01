from __future__ import annotations

from typing import Any
import logging
from dependency_injector.wiring import Provide
from lume_services.context import Context

from prefect.engine.result import Result
from lume_services.data.file import FileService


from typing import TypeVar, Optional, Generic
from pydantic import root_validator, Field
from pydantic.generics import GenericModel

from lume.serializers.base import SerializerBase
from lume_services.data.file.serializers import TextSerializer
from lume_services.utils import ObjLoader, JSON_ENCODERS


logger = logging.getLogger(__name__)

SerializerType = TypeVar("SerializerType", bound=SerializerBase)


class File(
    GenericModel,
    Generic[SerializerType],
    arbitrary_types_allowed=True,
    json_encoders=JSON_ENCODERS,
):
    filename: str
    loader: Optional[ObjLoader[SerializerType]]
    file_serializer: SerializerType = Field(exclude=True)

    @root_validator(pre=True)
    def validate_all(cls, values):
        serializer_type = cls.__fields__["serializer"].type_
        values["loader"] = ObjLoader[serializer_type]()
        values["serializer"] = values["loader"].load()

        return values

    def write(self, obj):
        self.serializer.serialize(self.filename, obj)


TextFile = File[TextSerializer]


class FileResult(Result):
    """Result written via file service. Location is the filepath."""

    def __init__(
        self,
        filesystem_identifier: str,
        serializer: SerializerBase,
        file_service: FileService = Provide[Context.file_service],
        **kwargs: Any,
    ) -> None:
        """Initialize FileResult

        Args:
            filesystem_identifier (str): String identifier for filesystem
            serializer (SerializerBase): Serializer for serializing result object value
                to filesystem
            file_service (FileService): Service for managing filesystem context
            **kwargs (Any, optional): any additional `Result` initialization options

        """
        self._file_service = file_service
        self._filesystem_identifier = filesystem_identifier
        self._serializer = serializer

        super().__init__(**kwargs)

    def read(self, location: str) -> FileResult:
        """Reads result from file service and return the corresponding result.

        Args:
            location (str): the location to read from
        Returns:
            Result: New result instantiated from location

        """
        new = self.copy()
        new.location = location

        logger.debug("Reading file result from %s...", location)

        new.value = self._file_service.read(
            self._filesystem_identifier, location, self._serializer
        )

        logger.debug("Finished reading result from {}...".format(location))

        return new

    def write(self, value: Any, create_dir=True, **kwargs: Any) -> FileResult:
        """Writes result using the file service

        Args:
            value (Any): Value to write
            **kwargs (optional): if provided, will be used to format the location
                template to determine the location to write to

        Returns:
            Result: returns a new result with specified save location

        """
        new = self.format(value=value, **kwargs)
        new.value = value
        assert new.location is not None

        logger.debug("Saving {}...".format(new.location))

        self._file_service.write(
            self._filesystem_identifier,
            new.location,
            new.value,
            self._serializer,
            create_dir=create_dir,
        )

        self.logger.debug("Finished uploading result to {}...".format(new.location))

        return new

    def exists(self, location: str, **kwargs: Any) -> bool:
        """Checks whether the target result exists using the file service.

        Args:
            location (str): Location of result in given file service.
            **kwargs (Any): string format arguments for `location`

        Returns:
            - bool: whether or not the target result exists
        """
        return self._file_service.file_exists(location)
