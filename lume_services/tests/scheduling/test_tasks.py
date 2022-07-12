from prefect import Flow, task
import pytest
from dependency_injector.containers import DynamicContainer
from datetime import datetime

from lume_services.data.results import (
    Result,
    ImpactResult,
)
from lume_services.data.files import HDF5File, ImageFile
from lume_services.tests.files import SAMPLE_IMPACT_ARCHIVE, SAMPLE_IMAGE_FILE
from lume_services.services.scheduling.tasks import (
    LoadDBResult,
    SaveDBResult,
    LoadFile,
    SaveFile,
    configure_services,
)
from lume_services.tests.files import SAMPLE_TEXT_FILE
from lume_services.data.files import TextFile
from lume_services.tests.fixtures.services.results import *  # noqa: F403, F401
from lume_services.tests.fixtures.services.files import *  # noqa: F403, F401
from lume_services.tests.fixtures.services.scheduling import *  # noqa: F403, F401

from lume_services import config


@pytest.fixture(scope="module", autouse=True)
def impact_result():
    return ImpactResult(
        flow_id="test_flow_id",
        inputs={"input1": 2.0, "input2": [1, 2, 3, 4, 5], "input3": "my_file.txt"},
        outputs={
            "output1": 2.0,
            "output2": [1, 2, 3, 4, 5],
            "output3": "my_file.txt",
        },
        plot_file=ImageFile(filename=SAMPLE_IMAGE_FILE, filesystem_identifier="local"),
        archive=HDF5File(filename=SAMPLE_IMPACT_ARCHIVE, filesystem_identifier="local"),
        pv_collection_isotime=datetime.now(),
        config={"config1": 1, "config2": 2},
    )


@pytest.fixture(scope="module", autouse=True)
def generic_result():
    return Result(
        flow_id="test_flow_id",
        inputs={"input1": 2.0, "input2": [1, 2, 3, 4, 5]},
        outputs={
            "output1": 2.0,
            "output2": [1, 2, 3, 4, 5],
        },
    )


class TestDBTaskResults:
    def test_save_db_result_task(self, results_db_service, generic_result):

        save_db_result = SaveDBResult()

        with Flow("save_db_result_task_flow") as flow:
            my_task = save_db_result(
                generic_result, results_db_service=results_db_service
            )

        flow_run = flow.run()

        assert flow_run.is_successful()
        assert flow_run.result[my_task].is_successful()
        assert flow_run.result[my_task].result == generic_result.unique_rep()

    def test_load_db_result_task(self, results_db_service, generic_result):

        load_db_result = LoadDBResult()

        result_rep = generic_result.unique_rep()

        with Flow("load_db_result_task_flow") as flow:
            my_task = load_db_result(
                result_rep,
                "inputs",
                attribute_index=["input1"],
                results_db_service=results_db_service,
            )

        flow_run = flow.run()

        assert flow_run.is_successful()
        assert flow_run.result[my_task].is_successful()
        assert flow_run.result[my_task].result == generic_result.inputs["input1"]

    def test_db_result_propogation(self, results_db_service, generic_result):

        result_rep = generic_result.unique_rep()

        load_db_result = LoadDBResult()

        @task
        def return_result(result):
            return result

        with Flow("load_db_result_task_flow") as flow:
            my_task = load_db_result(
                result_rep,
                "inputs",
                attribute_index=["input1"],
                results_db_service=results_db_service,
            )
            downstream_task = return_result(my_task)

        flow_run = flow.run()

        assert flow_run.is_successful()
        assert flow_run.result[my_task].is_successful()
        assert flow_run.result[downstream_task].is_successful()
        assert (
            flow_run.result[downstream_task].result == generic_result.inputs["input1"]
        )


class TestFileTaskResults:
    def test_save_file_task(self, tmp_path, file_service):

        save_file = SaveFile()

        filepath = f"{tmp_path}/tmp_file.txt"
        text = "text"
        text_file = TextFile(obj=text, filename=filepath, filesystem_identifier="local")

        with Flow("save_file_task_flow") as flow:
            my_task = save_file(
                obj=text,
                file_type=TextFile,
                filename=filepath,
                filesystem_identifier="local",
                file_service=file_service,
            )

        flow_run = flow.run()
        assert flow_run.is_successful()
        assert flow_run.result[my_task].is_successful()
        assert flow_run.result[my_task].result == text_file.jsonable_dict()

    def test_load_file_task(self, file_service):

        load_file = LoadFile()

        text_file = TextFile(filename=SAMPLE_TEXT_FILE, filesystem_identifier="local")
        text_file_rep = text_file.jsonable_dict()

        with Flow("load_file_task_flow") as flow:
            my_task = load_file(text_file_rep, file_service=file_service)

        flow_run = flow.run()
        assert flow_run.is_successful()
        assert flow_run.result[my_task].is_successful()
        assert flow_run.result[my_task].result == text_file.read(
            file_service=file_service
        )

    def test_file_result_propogation(self, file_service):

        load_file = LoadFile()

        text_file = TextFile(filename=SAMPLE_TEXT_FILE, filesystem_identifier="local")
        text_file_rep = text_file.jsonable_dict()

        @task
        def return_text(text):
            return text

        with Flow("load_file_task_flow") as flow:
            my_task = load_file(text_file_rep, file_service=file_service)
            downstream_task = return_text(my_task)

        flow_run = flow.run()
        assert flow_run.is_successful()
        assert flow_run.result[my_task].is_successful()
        assert flow_run.result[downstream_task].is_successful()
        assert flow_run.result[downstream_task].result == text_file.read(
            file_service=file_service
        )


class TestServiceConfiguration:
    @classmethod
    def setup_class(cls):
        config.context = None

    def test_service_config_task(self):

        assert config.context is None

        with Flow("configure") as flow:
            my_task = configure_services()

        flow_run = flow.run()
        assert flow_run.is_successful()
        assert flow_run.result[my_task].is_successful()
        assert config.context is not None
        assert isinstance(config.context, (DynamicContainer,))
