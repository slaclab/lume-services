import pytest

from datetime import timedelta

import yaml
from prefect.backend import TaskRunView
from prefect.backend.flow_run import stream_flow_run_logs

from lume_services.tasks.db import LoadDBResult
from lume_services.tests.files import FLOW_OF_FLOWS_YAML
from lume_services.tests.files.flows.flow1 import flow as flow1, append_text
from lume_services.tests.files.flows.flow2 import flow as flow2
from lume_services.tests.files.flows.flow3 import flow as flow3

from lume_services.files import TextFile
from lume_services.results import get_result_from_string

from lume_services.flows.flow_of_flows import FlowOfFlows


@pytest.fixture(scope="session", autouse=True)
def project_name(prefect_client):
    project_name = "test"
    prefect_client.create_project(project_name=project_name)
    return project_name


@pytest.fixture(scope="session", autouse=True)
def flow1_id(project_name, prefect_client):
    return flow1.register(project_name=project_name, labels=["lume-services"])


@pytest.fixture(scope="session", autouse=True)
def flow2_id(project_name, prefect_client):
    return flow2.register(project_name=project_name, labels=["lume-services"])


@pytest.fixture(scope="session", autouse=True)
def flow3_id(project_name, prefect_client):
    return flow3.register(project_name=project_name, labels=["lume-services"])


class TestFlows:
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
        prefect_client,
        flow1_id,
        docker_run_config,
        flow1_filename,
        mounted_filesystem,
    ):

        flow_run_id = prefect_client.create_flow_run(
            flow_id=flow1_id,
            parameters={
                "text1": self.text1,
                "text2": self.text2,
                "filename": flow1_filename,
                "filesystem_identifier": mounted_filesystem.identifier,
            },
            run_config=docker_run_config.build(),  # convert to prefect RunConfig
        )

        # watch and block
        stream_flow_run_logs(flow_run_id, max_duration=timedelta(minutes=1))

        configure_task = flow1.get_tasks(name="configure_services")[0]

        # check config task run
        config_task_run = TaskRunView.from_task_slug(
            configure_task.slug,
            flow_run_id,
        )
        assert config_task_run.state.is_successful()

        file_task = flow1.get_tasks(name="save_text_file")[0]

        task_run = TaskRunView.from_task_slug(
            file_task.slug,
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
        prefect_client,
        flow2_id,
        docker_run_config,
        test_flow1_run,
        results_db_service,
    ):

        flow_run_id = prefect_client.create_flow_run(
            flow_id=flow2_id,
            parameters={"file_rep": test_flow1_run},
            run_config=docker_run_config.build(),  # convert to prefect RunConfig
        )

        # watch and block
        stream_flow_run_logs(flow_run_id, max_duration=timedelta(minutes=1))

        # check config task run
        configure_task = flow2.get_tasks(name="configure_services")[0]
        config_task_run = TaskRunView.from_task_slug(
            configure_task.slug,
            flow_run_id,
        )
        assert config_task_run.state.is_successful()

        # check db result
        save_db_result = flow2.get_tasks(name="save_db_result")[0]
        task_run = TaskRunView.from_task_slug(
            save_db_result.slug,
            flow_run_id,
        )
        result_rep = task_run.get_result()

        # now load result as result object...
        result_type = get_result_from_string(result_rep["result_type_string"])
        result = result_type.load_from_query(
            result_rep["query"], results_db_service=results_db_service
        )

        assert task_run.state.is_successful()
        assert result.flow_id == flow2_id
        assert result.outputs["output1"] == f"{self.text1}{self.text2}"
        return result_rep

    def test_flow3_run(
        self,
        prefect_client,
        flow3_id,
        docker_run_config,
        test_flow2_run,
        results_db_service,
    ):

        # want to bind our task kwargs to flow2 outputs
        db_result = LoadDBResult().run(
            test_flow2_run,
            attribute="outputs",
            attribute_index=["output1"],
            results_db_service=results_db_service,
        )

        flow_run_id = prefect_client.create_flow_run(
            flow_id=flow3_id,
            parameters={"text1": db_result, "text2": f"{self.text1}{self.text2}"},
            run_config=docker_run_config.build(),  # convert to prefect RunConfig
        )

        # watch and block
        stream_flow_run_logs(flow_run_id, max_duration=timedelta(minutes=1))

        # check equivalence result
        check_text_equivalence = flow3.get_tasks(name="check_text_equivalence")[0]
        task_run = TaskRunView.from_task_slug(
            check_text_equivalence.slug,
            flow_run_id,
        )
        result = task_run.get_result()
        assert result


class TestFlowOfFlows:
    def test_load_yaml(self):
        with open(FLOW_OF_FLOWS_YAML, "r") as file:
            _ = yaml.safe_load(file)

    def test_validate_yaml(self, flow1_id, flow2_id, flow3_id):
        _ = FlowOfFlows.from_yaml(FLOW_OF_FLOWS_YAML)
