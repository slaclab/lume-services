from typing import Any, Literal
from pydantic import validator
import os
import logging

from .local import LocalFilesystem
from lume_services.errors import PathNotInMount
from lume.serializers.base import SerializerBase

logger = logging.getLogger(__name__)


_HostMountLiteral = Literal[
    "Directory",
    "DirectoryOrCreate",
    # "File",
    # "FileOrCreate",
    # "Socket",
    # "CharDevice",
    # "BlockDevice",
]


class MountedFilesystem(LocalFilesystem):
    """Handler for mounted filesystem. Modifies the LocalFilesystem to implements
    checks for mount path modifications. Container and container orchestration tools
    often allow the ability to provide an alias for a mounted directory. This handler
    accounts for the mount base and verifies that the file is within the path.

    """

    identifier: str = "mounted"
    mount_path: str
    mount_alias: str
    mount_type: _HostMountLiteral = "DirectoryOrCreate"

    # TODO[pydantic]: We couldn't refactor the `validator`, please replace it by `field_validator` manually.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-validators for more information.
    @validator("mount_path", pre=True)
    def validate_mount_path(cls, v, values):
        mount_type = values.get("mount_type")

        if mount_type == "DirectoryOrCreate":
            os.mkdir(v)

        return v

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
        print(path)

        if self.mount_alias in path:
            return path

        elif self.mount_path in path:
            return path.replace(self.mount_path, self.mount_alias)

        else:
            raise PathNotInMount(
                self.identifier, path, self.mount_path, self.mount_alias
            )
