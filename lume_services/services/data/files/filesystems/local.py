import os
from typing import Any
import logging

from .filesystem import Filesystem
from lume.serializers.base import SerializerBase

logger = logging.getLogger(__name__)


class LocalFilesystem(Filesystem):
    """Handler for local filesystem."""

    identifier: str = "local"

    def dir_exists(self, dir: str, create_dir: bool = False) -> bool:
        """Check that a directory exists on the local filesystem.

        Args:
            dir (str): Path of directory
            create_dir (bool): Whether to create directory if it does not exist

        Returns:
            bool

        """
        # use absolute path
        path = os.path.abspath(dir)
        if os.path.isdir(path):
            logger.info("Found directory %s on local filesystem.", path)
            return True

        # if creating...
        if create_dir:
            self.create_dir(path)
            return True
        else:
            logger.info("Unable to find directory %s on local filesystem.", path)
            return False

    def file_exists(self, filepath: str) -> bool:
        """Check that a file exists on the local filesystem.

        Args:
            filepath (str): Path to file

        Returns:
            bool

        """
        path = os.path.abspath(filepath)
        if os.path.isfile(path):
            logger.info("Found file %s on local filesystem.", path)
            return True

        else:
            logger.info("Unable to find file %s on local filesystem.", path)
            return False

    def create_dir(self, dir: str) -> None:
        """Create a directory on the local filesystem.

        Args:
            dir (str): Directory path to create

        """
        try:
            os.makedirs(dir, exist_ok=False)
        except Exception as e:
            logger.error("Unable to create directory %s on local filesystem.", dir)
            raise e

    def read(self, filepath: str, serializer: SerializerBase) -> Any:
        """Read file from the local filesystem.

        Args:
            filepath (str): Path of file to read.
            serializer (SerializerBase): Implementation of lume-base SerializerBase
                abstract base class.

        """
        path = os.path.abspath(filepath)
        content = serializer.deserialize(path)
        return content

    def write(
        self,
        filepath: str,
        object: Any,
        serializer: SerializerBase,
        create_dir: bool = False,
    ) -> None:
        """Write a file to the local filesystem.

        Args:
            filepath (str):
            object (Any): Object to serialize
            serializer (SerializerBase): Implementation of lume-base SerializerBase
                abstract base class
            create_dir (bool): Whether to create directory in case not implemented

        """
        path = os.path.abspath(filepath)
        dir = os.path.dirname(path)

        if create_dir and not self.dir_exists(dir):
            self.create_dir(dir)

        serializer.serialize(path, object)
