from typing import Any, Literal
import logging

from .local import LocalFilesystem
from lume.serializers.base import SerializerBase

logger = logging.getLogger(__name__)


_HostMountLiteral = Literal[
    "Directory",
    "DirectoryOrCreate",
    "File",
    "FileOrCreate",
    "Socket",
    "CharDevice",
    "BlockDevice",
]


class PathNotInMount(Exception):
    def __init__(
        self, filesystem_identifier: str, path: str, mount_path: str, mount_alias: str
    ):
        self.filesystem_identifier = filesystem_identifier
        self.mount_path = mount_path
        self.mount_alias = mount_alias
        self.message = "Path %s not in mount for mounted filesystem identifier: %s, \
            Mount path: %s, Mount alias: %s"
        super().__init__(
            self.message,
            self.path,
            self.filesystem_identifier,
            self.mount_path,
            self.mount_alias,
        )


class MountedFilesystem(LocalFilesystem):
    """Handler for mounted filesystem. Modifies the LocalFilesystem to implements
    checks for mount path modifications. Container and container orchestration tools
    often allow the ability to provide an alias for a mounted directory. This handler
    accounts for the mount base and verifies that the file is within the path.

    """

    identifier: str = "mounted"
    mount_path: str
    mount_alias: str
    mount_type: _HostMountLiteral = "Directory"

    def dir_exists(self, dir: str, create_dir: bool = False) -> bool:
        """Check that a directory exists on the mounted filesystem.

        Args:
            dir (str): Path of directory
            create_dir (bool): Whether to create directory if it does not exist

        Returns:
            bool

        """
        dir = self._check_mounted_path(dir)
        return super().dir_exists(dir, create_dir=create_dir)

    def file_exists(self, filepath: str) -> bool:
        """Check that a file exists on the mounted filesystem.

        Args:
            filepath (str): Path to file

        Returns:
            bool

        """

        filepath = self._check_mounted_path(filepath)
        return super().file_exists(filepath)

    def create_dir(self, dir: str) -> None:
        """Create a directory on the mounted filesystem.

        Args:
            dir (str): Directory path to create

        """
        dir = self._check_mounted_path(dir)
        super().create_dir(dir)

    def read(self, filepath: str, serializer: SerializerBase) -> Any:
        """Read file from the mounted filesystem.

        Args:
            filepath (str): Path of file to read
            serializer (SerializerBase): Implementation of lume-base SerializerBase
                abstract base class

        """
        filepath = self._check_mounted_path(filepath)
        return super().read(filepath, serializer)

    def write(
        self,
        filepath: str,
        object: Any,
        serializer: SerializerBase,
        create_dir: bool = False,
    ) -> None:
        """Write a file to the mounted filesystem.

        Args:
            filepath (str):
            object (Any): Object to serialize
            serializer (SerializerBase): Implementation of lume-base SerializerBase
                abstract base class
            create_dir (bool): Whether to create directory in case not implemented

        """
        filepath = self._check_mounted_path(filepath)
        super().write(filepath, object, serializer, create_dir=create_dir)

    def _check_mounted_path(self, path: str):
        """Checks that the path exists inside the mount point relative to mount path or
            alias.

        Args:
            path (str): Path to validate

        """

        if self.mount_path in path:
            return path.replace(self.mount_path, self.mount_alias)

        elif self.mount_alias in path:
            return path

        else:
            raise PathNotInMount(
                self.identifier, path, self.mount_path, self.mount_alias
            )
