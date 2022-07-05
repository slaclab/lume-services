import pytest
import os

from lume_services.data.files import TextFile

from dependency_injector.containers import DynamicContainer

from lume_services import config
from lume_services.data.results import Result
from lume_services.tests.fixtures.services.results import *  # noqa: F403, F401
from lume_services.tests.fixtures.services.models import *  # noqa: F403, F401
from lume_services.tests.fixtures.services.files import *  # noqa: F403, F401


@pytest.fixture(scope="class", autouse=True)
def lume_service_settings(file_service, model_db_service, results_db_service):
    return config.LUMEServicesSettings()


class TestLumeSettings:
    @classmethod
    def setup_class(cls):
        config.context = None

    def test_list_environ(self):
        config.list_env_vars()

    def test_configure_from_env(
        self, file_service, model_db_service, results_db_service
    ):
        assert config.context is None
        config.configure()
        assert config.context is not None
        assert isinstance(config.context, (DynamicContainer,))

    def test_configure_from_settings(self, lume_service_settings):
        config.context = None
        assert config.context is None
        config.configure(lume_service_settings)
        assert config.context is not None
        assert isinstance(config.context, (DynamicContainer,))

    def test_configure_from_env_failure(self):
        mongodb_host = os.environ.pop("LUME_RESULTS_DB__HOST")

        with pytest.raises(config.EnvironmentNotConfiguredError):
            config.configure()

        os.environ["LUME_RESULTS_DB__HOST"] = mongodb_host

    @classmethod
    def teardown_class(cls):
        config.context = None


class TestFileServiceInjection:
    @pytest.fixture
    def configure(self, lume_service_settings):
        config.configure(lume_service_settings)

    def test_file_service_injection_local(
        self, tmp_path, local_filesystem_handler, configure
    ):
        filepath = f"{tmp_path}/tmp_file.txt"
        text = "test text"
        text_file = TextFile(
            obj=text,
            filename=filepath,
            filesystem_identifier=local_filesystem_handler.identifier,
        )
        text_file.write()

        new_text = text_file.read()
        assert new_text == text

    def test_file_service_injection_mounted(
        self, mounted_filesystem_handler, configure
    ):

        filepath = f"{mounted_filesystem_handler.mount_alias}/tmp_file.txt"
        text = "test text"
        text_file = TextFile(
            obj=text,
            filename=filepath,
            filesystem_identifier=mounted_filesystem_handler.identifier,
        )
        text_file.write()

        assert mounted_filesystem_handler.file_exists(filepath)

        # read
        new_text = text_file.read()
        assert new_text == text

    @classmethod
    def teardown_class(cls):
        config.context = None


class TestResultServiceInjection:
    @pytest.fixture
    def configure(self, lume_service_settings):
        config.configure(lume_service_settings)

    def test_result_insert_by_method(self, generic_result, configure):
        generic_result.insert()

    def test_result_load_from_query(self, generic_result, configure):
        new_generic_result = Result.load_from_query(
            {
                "flow_id": generic_result.flow_id,
                "inputs": generic_result.inputs,
                "outputs": generic_result.outputs,
            },
        )

        assert generic_result.flow_id == new_generic_result.flow_id
        assert generic_result.inputs == new_generic_result.inputs
        assert generic_result.outputs == new_generic_result.outputs

    @classmethod
    def setup_class(cls):
        config.context = None
