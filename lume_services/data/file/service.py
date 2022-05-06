from typing import List, Any
from lume_services.data.file.systems import Filesystem
from lume.serializers.base import SerializerBase

import logging

logger = logging.getLogger(__name__)


class FilesystemNotConfigured(Exception):
    def __init__(self, filesystem_identifier: str, configured_filesystems: List[str]):
        self.filesystem_identifier = filesystem_identifier
        self.configured_filesystems = configured_filesystems

        self.message = f"Filesystem {filesystem_identifier} not configured. \
            Available filesystems are: {','.join(configured_filesystems)}"
        super().__init__(self.message)


class FileService:
    """Allows saving and retrieval to multiple file storage locations."""

    def __init__(self, filesystems: List[Filesystem]):
        """

        Args:
            filesystems (List[Filesystem]): List of filesystems

        """
        self._filesystems = {
            filesystem.identifier: filesystem for filesystem in filesystems
        }

    def dir_exists(
        self, filesystem_identifier: str, dir: str, create_dir: bool = True
    ) -> bool:
        """Check that a directory exists in a filesystem.

        Args:
            filesystem_identifier (str): String dentifier for filesystem
            dir (str): Directory path
            create_dir (bool): Whether to create directory in case not implemented

        Returns:
            bool

        """
        self._filesystem.dir_exists(dir, create_dir=create_dir)

    def file_exists(self, filesystem_identifier: str, file: str) -> bool:
        """Check that a file exists in a filesystem.

        Args:
            filesystem_identifier (str): String dentifier for filesystem

        Returns:
            bool

        """

        filesystem = self._get_filesystem(filesystem_identifier)
        filesystem.file_exists(file)

    def create_dir(self, filesystem_identifier: str, dir: str) -> None:
        """Create a directory in a filesystem.

        Args:
            filesystem_identifier (str): String dentifier for filesystem
            dir (str): Directory path

        """
        filesystem = self._get_filesystem(filesystem_identifier)
        filesystem.create_dir(dir)

    def read(
        self, filesystem_identifier: str, file: str, serializer: SerializerBase
    ) -> Any:
        """Read file from a filesystem.

        Args:
            filesystem_identifier (str): String dentifier for filesystem
            file (str): Path of file to read
            serializer (SerializerBase): Implementation of lume-base SerializerBase
                abstract base class

        """
        filesystem = self._get_filesystem(filesystem_identifier)
        return filesystem.read(file, serializer)

    def write(
        self,
        filesystem_identifier: str,
        filepath: str,
        object: Any,
        serializer: SerializerBase,
        create_dir: bool = True,
    ):
        """Write a file to a filesystem.

        Args:
            filesystem_identifier (str): String dentifier for filesystem
            filepath (str): Save path for file
            object (Any): Object to serialize
            serializer (SerializerBase): Implementation of lume-base SerializerBase
                abstract base class
            create_dir (bool): Whether to create directory in case not implemented

        """
        filesystem = self._get_filesystem(filesystem_identifier)
        filesystem.write(filepath, object, serializer, create_dir=create_dir)

    def _get_filesystem(self, filesystem_identifier: str) -> Filesystem:
        """Get filesystem by identifier.

        Args:
            filesystem_identifier (str): Identifier for filesystem.

        Returns:
            Filesystem

        """

        filesystem = self._filesystems.get(filesystem_identifier, None)

        if not filesystem:
            logger.error()
            raise FilesystemNotConfigured(
                filesystem_identifier, list(self._filesystems.keys())
            )

        return filesystem
