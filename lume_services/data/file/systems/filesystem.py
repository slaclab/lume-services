from typing import Any
from abc import ABC, abstractmethod, abstractproperty
from lume.serializers.base import SerializerBase


class Filesystem(ABC):
    @abstractproperty
    def identifier(self) -> str:
        ...

    @abstractmethod
    def dir_exists(self, dir: str, create_dir: bool = False) -> bool:
        """Check that a directory exists

        Args:
            dir (str): Path of directory
            create_dir (bool): Whether to create directory if it does not exist

        Returns:
            bool
        """
        ...

    @abstractmethod
    def file_exists(self, filepath: str) -> bool:
        """Check that a file exists

        Args:
            filepath (str): Path to file

        Returns:
            bool

        """
        ...

    @abstractmethod
    def create_dir(self, dir: str) -> None:
        """Create a directory on the filesystem.

        Args:
            dir (str): Directory path to create

        """
        ...

    @abstractmethod
    def read(self, filepath: str, serializer: SerializerBase) -> Any:
        """Read file from the filesystem.

        Args:
            filepath (str): Path of file to read
            serializer (SerializerBase): Implementation of lume-base SerializerBase
                abstract base class

        """
        ...

    @abstractmethod
    def write(
        self,
        filepath: str,
        object: Any,
        serializer: SerializerBase,
        create_dir: bool = False,
    ) -> None:
        """Write a file to the filesystem.

        Args:
            filepath (str):
            object (Any): Object to serialize
            serializer (SerializerBase): Implementation of lume-base SerializerBase
                abstract base class
            create_dir (bool): Whether to create directory in case not implemented

        """
        ...
