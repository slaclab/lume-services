from lume_services.scheduling.prefect.results.file import FileResult
import cloudpickle

def test_local_filesystem_result_service_injection(context, tmp_path, text_serializer):

    filepath = f"{tmp_path}/tmp_file.txt"
    text = "test text"
    result = FileResult("local", value=text, location=filepath, serializer=text_serializer)


def test_local_filesystem_everything_is_pickleable_after_init(file_service, tmp_path, text_serializer):
    filepath = f"{tmp_path}/tmp_file.txt"
    text = "test text"
    result = FileResult("local", value=text, location=filepath, serializer=text_serializer, file_service=file_service)

    assert cloudpickle.loads(cloudpickle.dumps(result)) == result


def test_write_local_filesystem_result(file_service, tmp_path, text_serializer):
    filepath = f"{tmp_path}/tmp_file.txt"
    text = "test text"
    result = FileResult("local", location=filepath, serializer=text_serializer, file_service=file_service)
    result.write(text)
