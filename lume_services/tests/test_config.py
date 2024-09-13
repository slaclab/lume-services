import pytest
import os
import numpy as np

import prefect

from dependency_injector.containers import DynamicContainer

from lume_services import config
from lume_services.results import Result
from lume_services.files import TextFile
from lume_services.errors import EnvironmentNotConfiguredError


class TestLumeSettings:
    @classmethod
    def setup_class(cls):
        config.context = None

    def test_list_environ(self):
        env_vars = config.get_env_vars()
        assert isinstance(env_vars, (dict,))

    def test_configure_from_env(
        self, model_db_service, results_db_service, scheduling_service
    ):
        assert config.context is None
        config.configure()
        assert config.context is not None
        assert isinstance(config.context, (DynamicContainer,))

        assert config._settings.model_db.user == model_db_service._model_db.config.user
        assert (
            config._settings.model_db.password.get_secret_value()
            == model_db_service._model_db.config.password.get_secret_value()
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
            config._settings.results_db.password.get_secret_value()
            == results_db_service._results_db.config.password.get_secret_value()
        )
        assert (
            config._settings.results_db.database
            == results_db_service._results_db.config.database
        )

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
            config._settings.model_db.password.get_secret_value()
            == lume_services_settings.model_db.password.get_secret_value()
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
            config._settings.results_db.password.get_secret_value()
            == lume_services_settings.results_db.password.get_secret_value()
        )
        assert (
            config._settings.results_db.database
            == lume_services_settings.results_db.database
        )

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


class TestFileServiceInjection:
    @pytest.fixture(autouse=True, scope="class")
    def _prepare(self, lume_services_settings):
        config.configure(lume_services_settings)

    @pytest.mark.usefixtures("_prepare")
    def test_file_service_injection_local(self, tmp_path, local_filesystem):
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

    @pytest.mark.usefixtures("_prepare")
    def test_file_service_injection_mounted(self, mounted_filesystem, fs):

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
    @pytest.fixture(autouse=True, scope="class")
    def _prepare(self, lume_services_settings):
        config.configure(lume_services_settings)

    @pytest.fixture()
    def inserted_generic_result(self):
        return Result(
            project_name="generic",
            flow_id="test_inject",
            inputs={"input1": 2.0, "input2": np.array([1, 2, 3, 4, 5])},
            outputs={
                "output1": 2.0,
                "output2": np.array([1, 2, 3, 4, 5]),
            },
        )

    @pytest.mark.usefixtures("_prepare")
    def test_result_insert_by_method(self, inserted_generic_result):
        inserted_generic_result.insert()

    @pytest.mark.usefixtures("_prepare")
    def test_result_load_from_query(self, inserted_generic_result):
        Result.load_from_query(
            inserted_generic_result.project_name,
            {
                "flow_id": inserted_generic_result.flow_id,
                "inputs": inserted_generic_result.inputs,
                "outputs": inserted_generic_result.outputs,
            },
        )


class TestPrefectConfig:
    def test_prefect_config(self, lume_services_settings):
        prefect_config = lume_services_settings.prefect

        # check assignment, has already been applied
        assert prefect.config.debug == prefect_config.debug
        assert prefect.config.home_dir == prefect_config.home_dir

        # check server values
        for key, value in prefect_config.server.dict().items():
            attr = getattr(prefect.config.server, key)
            assert attr == value

        # check ui values
        for key, value in prefect_config.ui.dict().items():
            attr = getattr(prefect.config.server.ui, key)
            assert attr == value

        # check graphql values
        for key, value in prefect_config.telemetry.dict().items():
            attr = getattr(prefect.config.server.telemetry, key)
            assert attr == value

    def test_prefect_update_config(self, lume_services_settings):
        config.configure(lume_services_settings)

        prefect_config = lume_services_settings.prefect

        new_config = prefect_config.copy(deep=True)
        new_config.server.host = "0.0.0.0"
        new_config.server.host_port = 4000

        with prefect.context(config=new_config.apply()):

            # check server values
            for key, value in new_config.server.dict().items():
                attr = getattr(prefect.config.server, key)
                assert attr == value

            # check ui values
            for key, value in new_config.ui.dict().items():
                attr = getattr(prefect.config.server.ui, key)
                assert attr == value

            # check graphql values
            for key, value in new_config.telemetry.dict().items():
                attr = getattr(prefect.config.server.telemetry, key)
                assert attr == value

    def test_prefect_reset_config(self, lume_services_settings):
        config.configure(lume_services_settings)

        prefect_config = lume_services_settings.prefect

        with prefect.context(config=prefect_config.apply()):

            # check server values
            for key, value in prefect_config.server.dict().items():
                attr = getattr(prefect.config.server, key)
                assert attr == value

            # check ui values
            for key, value in prefect_config.ui.dict().items():
                attr = getattr(prefect.config.server.ui, key)
                assert attr == value

            # check graphql values
            for key, value in prefect_config.telemetry.dict().items():
                attr = getattr(prefect.config.server.telemetry, key)
                assert attr == value
