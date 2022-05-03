import pytest

def test_local_filesystem_dir_exists(local_filesystem_handler, tmp_path):

    assert local_filesystem_handler.dir_exists(tmp_path, create_dir=False)


def test_local_filesystem_create_dir(local_filesystem_handler, tmp_path):

    new_tmp_dir = f"{tmp_path}/placeholder_dr"
    local_filesystem_handler.create_dir(new_tmp_dir)

    assert local_filesystem_handler.dir_exists(new_tmp_dir, create_dir=False)


def test_local_filesystem_dir_exist_create(local_filesystem_handler, tmp_path):

    new_tmp_dir = f"{tmp_path}/placeholder_dr"

    # create dir
    assert local_filesystem_handler.dir_exists(new_tmp_dir, create_dir=True)
    assert local_filesystem_handler.dir_exists(new_tmp_dir, create_dir=False)



def test_local_filesystem_read_write(local_filesystem_handler, tmp_path, text_serializer):

    tmp_file = f"{tmp_path}/test.txt"
    text = "test text"

    #write
    local_filesystem_handler.write(tmp_file, text, text_serializer)

    assert local_filesystem_handler.file_exists(tmp_file)

    # read
    new_text = local_filesystem_handler.read(tmp_file, text_serializer)

    assert new_text == text


def test_local_filesystem_create_dir_on_write(local_filesystem_handler, tmp_path, text_serializer):


    tmp_file = f"{tmp_path}/tmp_dir2/test.txt"
    text = "test text"

    # fail on no directory creation 
    with pytest.raises(FileNotFoundError):
        local_filesystem_handler.write(tmp_file, text, text_serializer, create_dir=False)

    # succeed on creation
    local_filesystem_handler.write(tmp_file, text, text_serializer, create_dir=True)
