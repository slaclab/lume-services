import pytest
import os

from lume_services.files import TextFile

from dependency_injector.containers import DynamicContainer

from lume_services import config
from lume_services.results import Result
from lume_services.errors import EnvironmentNotConfiguredError
from lume_services.services.files.filesystems.mounted import MountedFilesystem

from prefect.utilities.backend import load_backend, save_backend


class TestLumeSettings:
    @classmethod
    def setup_class(cls):
        config.context = None

    def test_list_environ(self):
        env_vars = config.list_env_vars()
        assert isinstance(env_vars, (dict,))

    def test_configure_from_env(
        self, file_service, model_db_service, results_db_service, scheduling_service
    ):
        save_backend("cloud")
        assert config.context is None
        config.configure()
        assert config.context is not None
        assert isinstance(config.context, (DynamicContainer,))

        # check that server has been applied
        backend_spec = load_backend()
        assert backend_spec["backend"] == "server"

        assert config._settings.model_db.user == model_db_service._model_db.config.user
        assert (
            config._settings.model_db.password
            == model_db_service._model_db.config.password
        )
        assert config._settings.model_db.host == model_db_service._model_db.config.host
        assert config._settings.model_db.port == model_db_service._model_db.config.port
        assert (
            config._settings.model_db.database
            == model_db_service._model_db.config.database
        )
        assert (
            config._settings.model_db.connection.pool_size
            == model_db_service._model_db.config.connection.pool_size
        )

        assert (
            config._settings.results_db.host
            == results_db_service._results_db.config.host
        )
        assert (
            config._settings.results_db.port
            == results_db_service._results_db.config.port
        )
        assert (
            config._settings.results_db.username
            == results_db_service._results_db.config.username
        )
        assert (
            config._settings.results_db.password
            == results_db_service._results_db.config.password
        )
        assert (
            config._settings.results_db.database
            == results_db_service._results_db.config.database
        )

        assert isinstance(config.context.mounted_filesystem(), (MountedFilesystem,))

        # prefect configuration
        assert (
            config._settings.prefect.server.host
            == scheduling_service.backend.config.server.host
        )
        assert (
            config._settings.prefect.server.host_port
            == scheduling_service.backend.config.server.host_port
        )
        assert (
            config._settings.prefect.server.tag
            == scheduling_service.backend.config.server.tag
        )

    def test_configure_from_settings(self, lume_services_settings):
        config.context = None
        assert config.context is None
        config.configure(lume_services_settings)
        assert config.context is not None
        assert isinstance(config.context, (DynamicContainer,))

        assert config._settings.model_db.user == lume_services_settings.model_db.user
        assert (
            config._settings.model_db.password
            == lume_services_settings.model_db.password
        )
        assert config._settings.model_db.host == lume_services_settings.model_db.host
        assert config._settings.model_db.port == lume_services_settings.model_db.port
        assert (
            config._settings.model_db.database
            == lume_services_settings.model_db.database
        )
        assert (
            config._settings.model_db.connection.pool_size
            == lume_services_settings.model_db.connection.pool_size
        )

        assert (
            config._settings.results_db.host == lume_services_settings.results_db.host
        )
        assert (
            config._settings.results_db.port == lume_services_settings.results_db.port
        )
        assert (
            config._settings.results_db.username
            == lume_services_settings.results_db.username
        )
        assert (
            config._settings.results_db.password
            == lume_services_settings.results_db.password
        )
        assert (
            config._settings.results_db.database
            == lume_services_settings.results_db.database
        )

        assert isinstance(config.context.mounted_filesystem(), (MountedFilesystem,))

        # prefect configuration
        assert (
            config._settings.prefect.server.host
            == lume_services_settings.prefect.server.host
        )
        assert (
            config._settings.prefect.server.host_port
            == lume_services_settings.prefect.server.host_port
        )
        assert (
            config._settings.prefect.server.tag
            == lume_services_settings.prefect.server.tag
        )

    def test_configure_from_env_failure(self):
        mongodb_host = os.environ.pop("LUME_RESULTS_DB__HOST")

        with pytest.raises(EnvironmentNotConfiguredError):
            config.configure()

        os.environ["LUME_RESULTS_DB__HOST"] = mongodb_host

    @classmethod
    def teardown_class(cls):
        save_backend("server")


class TestFileServiceInjection:
    def test_file_service_injection_local(
        self, tmp_path, local_filesystem, lume_services_settings
    ):
        filepath = f"{tmp_path}/tmp_file.txt"
        text = "test text"
        text_file = TextFile(
            obj=text,
            filename=filepath,
            filesystem_identifier=local_filesystem.identifier,
        )
        text_file.write(create_dir=True)

        new_text = text_file.read()
        assert new_text == text

    def test_file_service_injection_mounted(
        self, mounted_filesystem, lume_services_settings, fs
    ):

        filepath = f"{mounted_filesystem.mount_alias}/tmp_file.txt"
        text = "test text"
        text_file = TextFile(
            obj=text,
            filename=filepath,
            filesystem_identifier=mounted_filesystem.identifier,
        )
        text_file.write(create_dir=True)

        assert mounted_filesystem.file_exists(filepath)

        # read
        new_text = text_file.read()
        assert new_text == text

    @classmethod
    def teardown_class(cls):
        config.context = None


class TestResultServiceInjection:
    @pytest.fixture()
    def generic_result(self):
        return Result(
            flow_id="test_flow_id",
            inputs={"input1": 2.0, "input2": [1, 2, 3, 4, 5]},
            outputs={
                "output1": 2.0,
                "output2": [1, 2, 3, 4, 5],
            },
        )

    def test_result_insert_by_method(self, generic_result, lume_services_settings):
        generic_result.insert()

    def test_result_load_from_query(self, generic_result, lume_services_settings):
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
