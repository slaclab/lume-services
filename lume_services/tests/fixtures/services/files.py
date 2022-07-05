import pytest

from lume_services.services.data.files.filesystems import (
    LocalFilesystem,
    MountedFilesystem,
)
from lume_services.services.data.files import FileService


@pytest.fixture(scope="module")
def mount_path(tmp_path_factory):
    return str(tmp_path_factory.mktemp("mounted_dir"))


@pytest.fixture(scope="module", autouse=True)
def local_filesystem_handler():
    return LocalFilesystem()


@pytest.fixture(scope="module", autouse=True)
def mounted_filesystem_handler(mount_path):
    return MountedFilesystem(mount_path=mount_path, mount_alias="/User/my_user/data")


@pytest.fixture(scope="module")
def file_service(local_filesystem_handler, mounted_filesystem_handler):
    filesystems = [local_filesystem_handler, mounted_filesystem_handler]

    return FileService(filesystems)
