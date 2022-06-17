from lume_services.data.files import TextFile, ImageFile, YAMLFile
from PIL import Image

from lume_services.tests.files import SAMPLE_IMAGE_FILE, SAMPLE_YAML_FILE
import os

# Skipping H5PYFile because h5py serializer requires lume-base object
# see https://github.com/slaclab/lume-base/blob/main/lume/serializers/hdf5.py


class TestTextFile:
    def test_write_text_file(self, tmp_path, context):
        filepath = f"{tmp_path}/tmp_file.txt"
        text_file = TextFile(filename=filepath, file_system_identifier="local")
        text = "test text"
        text_file.write(text, context.file_service())

    def test_read_write_text_file(self, tmp_path, context):
        filepath = f"{tmp_path}/tmp_file.txt"
        text_file = TextFile(filename=filepath, file_system_identifier="local")
        text = "test text"
        text_file.write(text, context.file_service())

        new_text = text_file.read(context.file_service())
        assert new_text == text


class TestImageFile:
    def test_write_image_file(self, tmp_path, context):
        filepath = f"{tmp_path}/tmp_file.png"
        image_file = ImageFile(filename=filepath, file_system_identifier="local")
        image = Image.open(SAMPLE_IMAGE_FILE)
        image_file.write(image, context.file_service())
        assert os.path.isfile(filepath)

    def test_read_image_file(self, context):
        image_file = ImageFile(
            filename=SAMPLE_IMAGE_FILE, file_system_identifier="local"
        )
        image = image_file.read(context.file_service())
        assert isinstance(image, (Image.Image,))


class TestYAMLFile:
    def test_write_yaml_file(self, tmp_path, context):
        filepath = f"{tmp_path}/tmp_file.yaml"
        yaml_file = YAMLFile(filename=filepath, file_system_identifier="local")
        yaml_file.write(
            {"example_struct": ["item1", "item2", "item3"]}, context.file_service()
        )
        assert os.path.isfile(filepath)

    def test_read_yaml_file(self, context):
        yaml_file = YAMLFile(filename=SAMPLE_YAML_FILE, file_system_identifier="local")
        yaml = yaml_file.read(context.file_service())
        assert isinstance(yaml, (dict,))
