from lume_services.scheduling.files import (
    TextFile,
    load_file,
)

from lume_services.data.file.serializers import TextSerializer
import os


def test_local_filesystem_result(context, tmp_path):

    filepath = f"{tmp_path}/tmp_file.txt"
    text = "test text"
    text_serializer = TextSerializer()
    txt_file = TextFile(
        filename=filepath, file_system_identifier="local", serializer=text_serializer
    )
    txt_file.write(text, file_service=context.file_service())

    assert os.path.isfile(filepath)


def test_load_file_result_task(context, tmp_path):
    filepath = f"{tmp_path}/tmp_file.txt"
    text = "test text"
    text_serializer = TextSerializer()
    txt_file = TextFile(
        filename=filepath, file_system_identifier="local", serializer=text_serializer
    )
    txt_file.write(text, file_service=context.file_service())

    txt_file_json = txt_file.json()

    loaded_text = load_file.run(txt_file_json, file_service=context.file_service())

    assert loaded_text == text
