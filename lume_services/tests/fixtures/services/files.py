import pytest

from lume_services.services.files import FileService


@pytest.fixture(scope="session")
def file_service(local_filesystem, mounted_filesystem):
    filesystems = [local_filesystem, mounted_filesystem]

    return FileService(filesystems)
