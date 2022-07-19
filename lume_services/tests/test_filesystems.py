import pytest
from lume_services.services.files.filesystems import (
    MountedFilesystem,
    LocalFilesystem,
    PathNotInMount,
)
from lume_services.files.serializers.text import TextSerializer


@pytest.fixture(scope="module", autouse=True)
def text_serializer():
    return TextSerializer()


class TestLocalFilesystem:
    @pytest.fixture()
    def test_local_filesystem(self, tmp_path):
        return LocalFilesystem()

    def test_local_filesystem_dir_exists(self, test_local_filesystem, tmp_path):
        assert test_local_filesystem.dir_exists(tmp_path, create_dir=False)

    def test_local_filesystem_create_dir(self, test_local_filesystem, tmp_path):
        new_tmp_dir = f"{tmp_path}/placeholder_dr"
        test_local_filesystem.create_dir(new_tmp_dir)

        assert test_local_filesystem.dir_exists(new_tmp_dir, create_dir=False)

    def test_local_filesystem_dir_exist_create(self, test_local_filesystem, tmp_path):

        new_tmp_dir = f"{tmp_path}/placeholder_dr"

        # create dir
        assert test_local_filesystem.dir_exists(new_tmp_dir, create_dir=True)
        assert test_local_filesystem.dir_exists(new_tmp_dir, create_dir=False)

    def test_local_filesystem_read_write(
        self, test_local_filesystem, tmp_path, text_serializer
    ):

        tmp_file = f"{tmp_path}/test.txt"
        text = "test text"

        # write
        test_local_filesystem.write(tmp_file, text, text_serializer)

        assert test_local_filesystem.file_exists(tmp_file)

        # read
        new_text = test_local_filesystem.read(tmp_file, text_serializer)

        assert new_text == text

    def test_local_filesystem_create_dir_on_write(
        self, test_local_filesystem, tmp_path, text_serializer
    ):

        tmp_file = f"{tmp_path}/tmp_dir2/test.txt"
        text = "test text"

        # fail on no directory creation
        with pytest.raises(FileNotFoundError):
            test_local_filesystem.write(
                tmp_file, text, text_serializer, create_dir=False
            )

        # succeed on creation
        test_local_filesystem.write(tmp_file, text, text_serializer, create_dir=True)


class TestMountedFilesystem:
    @pytest.fixture()
    def test_mounted_filesystem(self, tmp_path, fs):
        return MountedFilesystem(mount_alias="/test_base", mount_path=str(tmp_path))

    def test_mounted_filesystem_dir_does_not_exist(self, test_mounted_filesystem):
        assert not test_mounted_filesystem.dir_exists(
            test_mounted_filesystem.mount_alias, create_dir=False
        )

    def test_mounted_filesystem_dir_does_not_exist_on_file_read(
        self, test_mounted_filesystem, text_serializer
    ):

        tmp_file = "/some_unknown_dir/test.txt"
        text = "test text"

        # write
        with pytest.raises(PathNotInMount):
            test_mounted_filesystem.write(
                tmp_file, text, text_serializer, create_dir=False
            )

    def test_mounted_filesystem_dir_exists(self, test_mounted_filesystem):
        assert test_mounted_filesystem.dir_exists(
            test_mounted_filesystem.mount_alias, create_dir=True
        )

    def test_mounted_filesystem_create_dir(self, test_mounted_filesystem):

        new_tmp_dir = f"{test_mounted_filesystem.mount_alias}/placeholder_dir"
        test_mounted_filesystem.create_dir(new_tmp_dir)

        assert test_mounted_filesystem.dir_exists(new_tmp_dir, create_dir=False)

    def test_mounted_filesystem_dir_exist_create(self, test_mounted_filesystem):

        new_tmp_dir = f"{test_mounted_filesystem.mount_alias}/placeholder_dir"

        # create dir
        assert test_mounted_filesystem.dir_exists(new_tmp_dir, create_dir=True)
        assert test_mounted_filesystem.dir_exists(new_tmp_dir, create_dir=False)

    def test_mounted_filesystem_read_write(
        self, test_mounted_filesystem, text_serializer
    ):

        tmp_file = f"{test_mounted_filesystem.mount_alias}/test.txt"
        text = "test text"

        # write
        test_mounted_filesystem.write(tmp_file, text, text_serializer, create_dir=True)

        assert test_mounted_filesystem.file_exists(tmp_file)

        # read
        new_text = test_mounted_filesystem.read(tmp_file, text_serializer)

        assert new_text == text

    def test_mounted_filesystem_create_dir_on_write(
        self, test_mounted_filesystem, text_serializer
    ):

        tmp_file = f"{test_mounted_filesystem.mount_alias}/tmp_dir2/test.txt"
        text = "test text"

        # fail on no directory creation
        with pytest.raises(FileNotFoundError):
            test_mounted_filesystem.write(
                tmp_file, text, text_serializer, create_dir=False
            )

        # succeed on creation
        test_mounted_filesystem.write(tmp_file, text, text_serializer, create_dir=True)
