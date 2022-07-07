import pytest
from lume_services.services.data.files.filesystems import (
    MountedFilesystem,
    LocalFilesystem,
    PathNotInMount,
)
from lume_services.data.files.serializers.text import TextSerializer


@pytest.fixture(scope="module", autouse=True)
def text_serializer():
    return TextSerializer()


class TestLocalFilesystem:
    @pytest.fixture()
    def local_filesystem_handler(self, tmp_path):
        return LocalFilesystem()

    def test_local_filesystem_dir_exists(self, local_filesystem_handler, tmp_path):
        assert local_filesystem_handler.dir_exists(tmp_path, create_dir=False)

    def test_local_filesystem_create_dir(self, local_filesystem_handler, tmp_path):
        new_tmp_dir = f"{tmp_path}/placeholder_dr"
        local_filesystem_handler.create_dir(new_tmp_dir)

        assert local_filesystem_handler.dir_exists(new_tmp_dir, create_dir=False)

    def test_local_filesystem_dir_exist_create(
        self, local_filesystem_handler, tmp_path
    ):

        new_tmp_dir = f"{tmp_path}/placeholder_dr"

        # create dir
        assert local_filesystem_handler.dir_exists(new_tmp_dir, create_dir=True)
        assert local_filesystem_handler.dir_exists(new_tmp_dir, create_dir=False)

    def test_local_filesystem_read_write(
        self, local_filesystem_handler, tmp_path, text_serializer
    ):

        tmp_file = f"{tmp_path}/test.txt"
        text = "test text"

        # write
        local_filesystem_handler.write(tmp_file, text, text_serializer)

        assert local_filesystem_handler.file_exists(tmp_file)

        # read
        new_text = local_filesystem_handler.read(tmp_file, text_serializer)

        assert new_text == text

    def test_local_filesystem_create_dir_on_write(
        self, local_filesystem_handler, tmp_path, text_serializer
    ):

        tmp_file = f"{tmp_path}/tmp_dir2/test.txt"
        text = "test text"

        # fail on no directory creation
        with pytest.raises(FileNotFoundError):
            local_filesystem_handler.write(
                tmp_file, text, text_serializer, create_dir=False
            )

        # succeed on creation
        local_filesystem_handler.write(tmp_file, text, text_serializer, create_dir=True)


class TestMountedFilesystem:
    @pytest.fixture()
    def local_filesystem_handler(self):
        return LocalFilesystem()

    @pytest.fixture()
    def mounted_filesystem_handler(self, tmp_path, fs):
        return MountedFilesystem(mount_alias="/test_base", mount_path=str(tmp_path))

    def test_mounted_filesystem_dir_does_not_exist(self, mounted_filesystem_handler):
        assert not mounted_filesystem_handler.dir_exists(
            mounted_filesystem_handler.mount_alias, create_dir=False
        )

    def test_mounted_filesystem_dir_does_not_exist_on_file_read(
        self, mounted_filesystem_handler, text_serializer
    ):

        tmp_file = "/some_unknown_dir/test.txt"
        text = "test text"

        # write
        with pytest.raises(PathNotInMount):
            mounted_filesystem_handler.write(
                tmp_file, text, text_serializer, create_dir=False
            )

    def test_mounted_filesystem_dir_exists(self, mounted_filesystem_handler):
        assert mounted_filesystem_handler.dir_exists(
            mounted_filesystem_handler.mount_alias, create_dir=True
        )

    def test_mounted_filesystem_create_dir(self, mounted_filesystem_handler):

        new_tmp_dir = f"{mounted_filesystem_handler.mount_alias}/placeholder_dir"
        mounted_filesystem_handler.create_dir(new_tmp_dir)

        assert mounted_filesystem_handler.dir_exists(new_tmp_dir, create_dir=False)

    def test_mounted_filesystem_dir_exist_create(self, mounted_filesystem_handler):

        new_tmp_dir = f"{mounted_filesystem_handler.mount_alias}/placeholder_dir"

        # create dir
        assert mounted_filesystem_handler.dir_exists(new_tmp_dir, create_dir=True)
        assert mounted_filesystem_handler.dir_exists(new_tmp_dir, create_dir=False)

    def test_mounted_filesystem_read_write(
        self, mounted_filesystem_handler, text_serializer
    ):

        tmp_file = f"{mounted_filesystem_handler.mount_alias}/test.txt"
        text = "test text"

        # write
        mounted_filesystem_handler.write(
            tmp_file, text, text_serializer, create_dir=True
        )

        assert mounted_filesystem_handler.file_exists(tmp_file)

        # read
        new_text = mounted_filesystem_handler.read(tmp_file, text_serializer)

        assert new_text == text

    def test_mounted_filesystem_create_dir_on_write(
        self, mounted_filesystem_handler, text_serializer
    ):

        tmp_file = f"{mounted_filesystem_handler.mount_alias}/tmp_dir2/test.txt"
        text = "test text"

        # fail on no directory creation
        with pytest.raises(FileNotFoundError):
            mounted_filesystem_handler.write(
                tmp_file, text, text_serializer, create_dir=False
            )

        # succeed on creation
        mounted_filesystem_handler.write(
            tmp_file, text, text_serializer, create_dir=True
        )
