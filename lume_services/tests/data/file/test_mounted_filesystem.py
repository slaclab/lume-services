import pytest
from lume_services.data.file.systems.mounted import MountedFilesystem


@pytest.fixture(scope="module", autouse=True)
def mount_path():
    return "/test_base"


@pytest.fixture(scope="function", autouse=True)
def mounted_filesystem_handler(tmp_path, mount_path):
    # pretend we're mounting some filesystem to tmp_path
    return MountedFilesystem(mount_path, str(tmp_path))


def test_mounted_filesystem_dir_exists(mounted_filesystem_handler, mount_path):

    assert mounted_filesystem_handler.dir_exists(mount_path, create_dir=False)


def test_mounted_filesystem_dir_alias_exists(mounted_filesystem_handler):

    assert mounted_filesystem_handler.dir_exists(
        mounted_filesystem_handler._mount_alias, create_dir=False
    )


def test_mounted_filesystem_create_dir(mounted_filesystem_handler, mount_path):

    new_tmp_dir = f"{mount_path}/placeholder_dir"
    mounted_filesystem_handler.create_dir(new_tmp_dir)

    assert mounted_filesystem_handler.dir_exists(new_tmp_dir, create_dir=False)


def test_mounted_filesystem_dir_exist_create(mounted_filesystem_handler, mount_path):

    new_tmp_dir = f"{mount_path}/placeholder_dir"

    # create dir
    assert mounted_filesystem_handler.dir_exists(new_tmp_dir, create_dir=True)
    assert mounted_filesystem_handler.dir_exists(new_tmp_dir, create_dir=False)


def test_mounted_filesystem_read_write(
    mounted_filesystem_handler, mount_path, text_serializer
):

    tmp_file = f"{mount_path}/test.txt"
    text = "test text"

    # write
    mounted_filesystem_handler.write(tmp_file, text, text_serializer)

    assert mounted_filesystem_handler.file_exists(tmp_file)

    # read
    new_text = mounted_filesystem_handler.read(tmp_file, text_serializer)

    assert new_text == text


def test_mounted_filesystem_create_dir_on_write(
    mounted_filesystem_handler, mount_path, text_serializer
):

    tmp_file = f"{mount_path}/tmp_dir2/test.txt"
    text = "test text"

    # fail on no directory creation
    with pytest.raises(FileNotFoundError):
        mounted_filesystem_handler.write(
            tmp_file, text, text_serializer, create_dir=False
        )

    # succeed on creation
    mounted_filesystem_handler.write(tmp_file, text, text_serializer, create_dir=True)
