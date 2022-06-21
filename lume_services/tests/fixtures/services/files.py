import pytest

from lume_services.services.data.files.filesystems import (
    LocalFilesystem,
    MountedFilesystem,
)
from lume_services.services.data.files import FileService


@pytest.fixture(scope="module", autouse=True)
def local_filesystem_handler():
    return LocalFilesystem()


@pytest.fixture(scope="module", autouse=True)
def mounted_filesystem_handler():
    return MountedFilesystem()


@pytest.fixture(scope="module")
def file_service(local_filesystem_handler):
    filesystems = [local_filesystem_handler]

    return FileService(filesystems)
