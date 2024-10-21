import pytest

from datetime import timedelta

from prefect import Client
import prefect
import yaml
from prefect.backend import TaskRunView
from prefect.backend.flow_run import stream_flow_run_logs

from lume_services.tasks.db import LoadDBResult
from lume_services.tests.flows.lume_services_test_flows.flow1 import (
    flow as flow1,
    append_text,
)
from lume_services.tests.flows.lume_services_test_flows.flow2 import flow as flow2
from lume_services.tests.flows.lume_services_test_flows.flow3 import flow as flow3

from lume_services.files import TextFile
from lume_services.results import get_result_from_string
from lume_services.tests.files import FLOW_OF_FLOWS_YAML
from lume_services.flows.flow_of_flows import FlowOfFlows
from lume_services import config


@pytest.mark.usefixtures("scheduling_service")
@pytest.fixture(scope="module", autouse=True)
def project_name(lume_services_settings):

    config.configure(lume_services_settings)

    project_name = "test"

    prefect_config = lume_services_settings.prefect
    with prefect.context(config=prefect_config.apply()):
        client = Client()
        client.create_project(project_name=project_name)

    return project_name


@pytest.fixture(scope="module", autouse=True)
def flow1_id(project_name, lume_services_settings):

    prefect_config = lume_services_settings.prefect
    with prefect.context(config=prefect_config.apply()):
        return flow1.register(project_name=project_name, labels=["lume-services"])


@pytest.fixture(scope="module", autouse=True)
def flow2_id(project_name, lume_services_settings):

    prefect_config = lume_services_settings.prefect
    with prefect.context(config=prefect_config.apply()):
        return flow2.register(project_name=project_name, labels=["lume-services"])


@pytest.fixture(scope="module", autouse=True)
def flow3_id(project_name, lume_services_settings):

    prefect_config = lume_services_settings.prefect
    with prefect.context(config=prefect_config.apply()):
        return flow3.register(project_name=project_name, labels=["lume-services"])


class TestFlowExecution:
    text1 = "hey"
    text2 = " you"

    @pytest.fixture(scope="class")
    def flow1_filename(self, mounted_filesystem):
        return f"{mounted_filesystem.mount_alias}/flow1_res.txt"

    @pytest.fixture(scope="class")
    def flow1_filename_local(self, mounted_filesystem):
        return f"{mounted_filesystem.mount_path}/flow1_res.txt"

    @pytest.fixture()
    def test_flow1_run(
        self,
        flow1_id,
        docker_run_config,
        flow1_filename,
        mounted_filesystem,
        lume_services_settings,
    ):

        prefect_config = lume_services_settings.prefect
        with prefect.context(config=prefect_config.apply()):
            client = Client()

            flow_run_id = client.create_flow_run(
                flow_id=flow1_id,
                parameters={
                    "text1": self.text1,
                    "text2": self.text2,
                    "filename": flow1_filename,
                    "filesystem_identifier": mounted_filesystem.identifier,
                },
                run_config=docker_run_config.build(),  # convert to prefect
            )

            # watch and block
            stream_flow_run_logs(flow_run_id, max_duration=timedelta(minutes=1))

            configure_task = flow1.get_tasks(name="configure_lume_services")[0]
            configure_slug = flow1.slugs[configure_task]

            # check config task run
            config_task_run = TaskRunView.from_task_slug(
                configure_slug,
                flow_run_id,
            )
            assert config_task_run.state.is_successful()

            # check text result
            task = flow1.get_tasks(name="save_text_file")[0]
            slug = flow1.slugs[task]
            task_run = TaskRunView.from_task_slug(
                slug,
                flow_run_id,
            )

            # check task result
            assert task_run.state.is_successful()

            result = task_run.get_result()

            text = append_text.run(self.text1, self.text2)

            # create text file object
            text_file = TextFile(
                obj=text,
                filename=flow1_filename,
                filesystem_identifier=mounted_filesystem.identifier,
            )
            text_file_rep = text_file.jsonable_dict()

            assert result == text_file_rep
            return text_file_rep

    @pytest.fixture()
    def test_flow2_run(
        self,
        flow2_id,
        docker_run_config,
        test_flow1_run,
        results_db_service,
        lume_services_settings,
    ):
        prefect_config = lume_services_settings.prefect
        project_name = "test"
        with prefect.context(config=prefect_config.apply()):

            prefect_run_config = docker_run_config.build()
            # requires setting env variable for saving db result
            prefect_run_config.env.update(
                {"PREFECT__CONTEXT__PROJECT_NAME": project_name}
            )

            client = Client()

            flow_run_id = client.create_flow_run(
                flow_id=flow2_id,
                parameters={"file_rep": test_flow1_run},
                run_config=prefect_run_config,  # convert to prefect
            )

            # watch and block
            stream_flow_run_logs(flow_run_id, max_duration=timedelta(minutes=1))

            # check config task run
            configure_task = flow2.get_tasks(name="configure_lume_services")[0]
            configure_slug = flow2.slugs[configure_task]

            # check config task run
            config_task_run = TaskRunView.from_task_slug(
                configure_slug,
                flow_run_id,
            )
            assert config_task_run.state.is_successful()

            # check db result
            task = flow2.get_tasks(name="save_db_result")[0]
            slug = flow2.slugs[task]
            task_run = TaskRunView.from_task_slug(
                slug,
                flow_run_id,
            )
            result_rep = task_run.get_result()

            # now load result as result object...
            result_type = get_result_from_string(result_rep["result_type_string"])
            result = result_type.load_from_query(
                result_rep["project_name"],
                result_rep["query"],
                results_db_service=results_db_service,
            )

            assert task_run.state.is_successful()
            assert result.flow_id == flow2_id
            assert result.outputs["output1"] == f"{self.text1}{self.text2}"
            return result_rep

    @pytest.mark.skip()
    def test_flow3_run(
        self,
        flow3_id,
        docker_run_config,
        test_flow2_run,
        results_db_service,
        lume_services_settings,
    ):
        prefect_config = lume_services_settings.prefect
        with prefect.context(config=prefect_config.apply()):

            client = Client()

            # want to bind our task kwargs to flow2 outputs
            db_result = LoadDBResult().run(
                test_flow2_run,
                attribute_index=["outputs", "output1"],
                results_db_service=results_db_service,
            )

            flow_run_id = client.create_flow_run(
                flow_id=flow3_id,
                parameters={"text1": db_result, "text2": f"{self.text1}{self.text2}"},
                run_config=docker_run_config.build(),  # convert to prefect
            )

            # watch and block
            stream_flow_run_logs(flow_run_id, max_duration=timedelta(minutes=1))

            # check equivalence result
            task = flow3.get_tasks(name="check_text_equivalence")[0]
            slug = flow3.slugs[task]
            task_run = TaskRunView.from_task_slug(
                slug,
                flow_run_id,
            )
            result = task_run.get_result()
            assert result


@pytest.mark.skip()
class TestFlow:
    def test_flow_construction(self):
        ...


@pytest.mark.skip()
class TestFlowOfFlows:
    def test_load_yaml(self):
        with open(FLOW_OF_FLOWS_YAML, "r") as file:
            _ = yaml.safe_load(file)

    @pytest.mark.usefixtures("flow1_id", "flow2_id", "flow3_id")
    def test_validate_yaml(self, scheduling_service, lume_services_settings):

        with prefect.context(config=lume_services_settings.prefect.apply()):
            _ = FlowOfFlows.from_yaml(
                FLOW_OF_FLOWS_YAML, scheduling_service=scheduling_service
            )

    @pytest.mark.usefixtures("flow1_id", "flow2_id", "flow3_id")
    def test_compose(self, scheduling_service, lume_services_settings):
        with prefect.context(config=lume_services_settings.prefect.apply()):
            flow_of_flows = FlowOfFlows.from_yaml(
                FLOW_OF_FLOWS_YAML, scheduling_service=scheduling_service
            )
            flow_of_flows.compose(image_tag="pytest-flow-of-flows", local=True)

    @pytest.mark.skip()
    @pytest.mark.usefixtures("flow1_id", "flow2_id", "flow3_id")
    def test_flow_of_flows_id(
        self, project_name, lume_services_settings, scheduling_service
    ):
        with prefect.context(config=lume_services_settings.prefect.apply()):
            flow_of_flows = FlowOfFlows.from_yaml(
                FLOW_OF_FLOWS_YAML, scheduling_service=scheduling_service
            )
            flow_of_flows.compose(image_tag="pytest-flow-of-flows", local=True)

            flow_of_flows.prefect_flow.register(
                project_name=project_name, labels=["lume-services"]
            )
