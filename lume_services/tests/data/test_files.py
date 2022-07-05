import os
from PIL import Image
from impact import Impact
from lume_services.tests.files import (
    SAMPLE_IMAGE_FILE,
    SAMPLE_YAML_FILE,
    SAMPLE_IMPACT_ARCHIVE,
    SAMPLE_TEXT_FILE,
)
from lume_services.data.files import TextFile, ImageFile, YAMLFile, HDF5File
from lume_services.tests.fixtures.services.files import *  # noqa: F403, F401


class TestTextFile:
    def test_read_text_file(self, file_service):
        text_file = TextFile(filename=SAMPLE_TEXT_FILE, filesystem_identifier="local")
        text = text_file.read(file_service=file_service)
        assert isinstance(text, (str,))

    def test_write_text_file(self, tmp_path, file_service):
        filepath = f"{tmp_path}/tmp_file.txt"
        text = "test text"
        text_file = TextFile(obj=text, filename=filepath, filesystem_identifier="local")
        text_file.write(file_service=file_service)

    def test_read_write_text_file(self, tmp_path, file_service):
        filepath = f"{tmp_path}/tmp_file.txt"
        text = "test text"
        text_file = TextFile(obj=text, filename=filepath, filesystem_identifier="local")
        text_file.write(file_service=file_service)

        new_text = text_file.read(file_service=file_service)
        assert new_text == text

    def test_load_text_file(self, tmp_path, file_service):
        filepath = f"{tmp_path}/tmp_file.txt"
        text = "test text"
        text_file = TextFile(obj=text, filename=filepath, filesystem_identifier="local")
        text_file.write(file_service=file_service)

        new_text = text_file.read(file_service=file_service)
        assert new_text == text


class TestImageFile:
    def test_write_image_file(self, tmp_path, file_service):
        filepath = f"{tmp_path}/tmp_file.png"
        image_file = ImageFile(filename=filepath, filesystem_identifier="local")
        image = Image.open(SAMPLE_IMAGE_FILE)
        image_file.write(image, file_service=file_service)
        assert os.path.isfile(filepath)

    def test_read_image_file(self, file_service):
        image_file = ImageFile(
            filename=SAMPLE_IMAGE_FILE, filesystem_identifier="local"
        )
        image = image_file.read(file_service=file_service)
        assert isinstance(image, (Image.Image,))

    def test_load_image_file(self, file_service):
        image_file = ImageFile(
            filename=SAMPLE_IMAGE_FILE, filesystem_identifier="local"
        )
        image_file.load_file(file_service=file_service)
        assert isinstance(image_file.obj, (Image.Image,))


class TestYAMLFile:
    def test_write_yaml_file(self, tmp_path, file_service):
        filepath = f"{tmp_path}/tmp_file.yaml"
        yaml_file = YAMLFile(filename=filepath, filesystem_identifier="local")
        yaml_file.write(
            {"example_struct": ["item1", "item2", "item3"]},
            file_service=file_service,
        )
        assert os.path.isfile(filepath)

    def test_read_yaml_file(self, file_service):
        yaml_file = YAMLFile(filename=SAMPLE_YAML_FILE, filesystem_identifier="local")
        yaml = yaml_file.read(file_service=file_service)
        assert isinstance(yaml, (dict,))

    def test_load_yaml_file(self, file_service):
        yaml_file = YAMLFile(filename=SAMPLE_YAML_FILE, filesystem_identifier="local")
        yaml_file.load_file(file_service=file_service)
        assert isinstance(yaml_file.obj, (dict,))


class TestHDF5File:
    def test_read_hdf5_file(self, file_service):
        hdf5_file = HDF5File(
            filename=SAMPLE_IMPACT_ARCHIVE, filesystem_identifier="local"
        )
        impact_obj = hdf5_file.read(file_service=file_service)
        assert isinstance(impact_obj, (Impact,))

    def test_load_hdf5_file(self, file_service):
        hdf5_file = HDF5File(
            filename=SAMPLE_IMPACT_ARCHIVE, filesystem_identifier="local"
        )
        hdf5_file.load_file(file_service=file_service)
        assert isinstance(hdf5_file.obj, (Impact,))

    def test_write_hdf5_file(self, tmp_path, file_service):
        hdf5_file = HDF5File(
            filename=SAMPLE_IMPACT_ARCHIVE, filesystem_identifier="local"
        )
        impact_obj = hdf5_file.read(file_service=file_service)

        filepath = f"{tmp_path}/tmp_file.h5"
        new_hdf5_file = HDF5File(filename=filepath, filesystem_identifier="local")
        new_hdf5_file.write(impact_obj, file_service=file_service)

        # load existing
        assert os.path.isfile(filepath)
