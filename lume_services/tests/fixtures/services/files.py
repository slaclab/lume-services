import pytest

from lume_services.services.data.files import FileService


@pytest.fixture(scope="session")
def file_service(local_filesystem_handler, mounted_filesystem_handler):
    filesystems = [local_filesystem_handler, mounted_filesystem_handler]

    return FileService(filesystems)
