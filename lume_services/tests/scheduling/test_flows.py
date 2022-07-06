# https://docs.prefect.io/core/idioms/testing-flows.html
import pytest
from lume_services.tests.files import FLOW_OF_FLOWS_YAML
from lume_services.tests.files.flows.flow1 import flow1, append_text
from lume_services.tests.files.flows.flow2 import flow2
from lume_services.tests.files.flows.flow3 import flow3

from prefect.backend import TaskRunView
from prefect.backend.flow_run import stream_flow_run_logs
from prefect import Client

from datetime import timedelta
import yaml

from lume_services.data.files import TextFile
from lume_services.services.scheduling import (
    SchedulingService,
    load_flow_of_flows_from_yaml,
)
from lume_services.tests.fixtures.services.scheduling import *  # noqa: F403, F401
from lume_services.tests.fixtures.services.files import *  # noqa: F403, F401


def test_load_yaml():
    with open(FLOW_OF_FLOWS_YAML, "r") as file:
        flow_of_flow_config = yaml.safe_load(file)


# def test_validate_yaml():
#    flow_of_flows = load_flow_of_flows_from_yaml(FLOW_OF_FLOWS_YAML)


class TestFlows:
    project_name = "test_flows"
    flow1_filename = "flow1_res.txt"

    @pytest.fixture()
    def flow1_filename(self, mounted_filesystem_handler):
        return f"{mounted_filesystem_handler.mount_alias}/flow1_res.txt"

    @pytest.fixture()
    def client(self, prefect_api_str, prefect_docker_agent):
        client = Client(api_server=prefect_api_str)
        client.graphql("query{hello}", retry_on_api_error=False)
        return client

    def test_project_create(self, client):
        client.create_project(project_name=self.project_name)

    @pytest.fixture()
    def flow1_id(self):
        return flow1.register(project_name=self.project_name, labels=["lume-services"])

    @pytest.fixture()
    def flow2_id(self):
        return flow2.register(project_name=self.project_name, labels=["lume-services"])

    @pytest.fixture()
    def flow3_id(self):
        return flow3.register(project_name=self.project_name, labels=["lume-services"])

    def test_flow1_run_creation(
        self,
        client,
        flow1_id,
        docker_backend,
        docker_run_config,
        flow1_filename,
        mounted_filesystem_handler,
    ):
        text1 = "hey"
        text2 = " you"

        flow_run_id = client.create_flow_run(
            flow_id=flow1_id,
            parameters={
                "text1": text1,
                "text2": text2,
                "filename": flow1_filename,
                "filesystem_identifier": mounted_filesystem_handler.identifier,
            },
            run_config=docker_backend.get_run_config(docker_run_config),
        )

        # watch and block
        stream_flow_run_logs(flow_run_id, max_duration=timedelta(minutes=1))

        # create flow run view
        # flow_run = FlowRunView.from_flow_run_id(flow_run_id)
        task_run = TaskRunView.from_task_slug(
            "save_file-1",
            flow_run_id,
        )
        result = task_run.get_result()

        # check config task run
        config_task_run = TaskRunView.from_task_slug(
            "configure_services-1",
            flow_run_id,
        )
        assert config_task_run.state.is_successful()

        text = append_text.run(text1, text2)

        # create text file object
        text_file = TextFile(
            obj=text,
            filename=flow1_filename,
            filesystem_identifier=mounted_filesystem_handler.identifier,
        )
        text_file_rep = text_file.jsonable_dict()

        # check task result
        assert task_run.state.is_successful()
        assert result == text_file_rep

    def test_flow2_run_creation(
        self, client, flow2_id, docker_backend, docker_run_config
    ):
        file_rep = {
            "filesystem_identifier": "local",
            "filename": "flow1_res.txt",
            "file_type_string": "lume_services.data.files.TextFile",
        }

        flow_run_id = client.create_flow_run(
            flow_id=flow2_id,
            parameters={"file_rep": file_rep},
            run_config=docker_backend.get_run_config(docker_run_config),
        )

        # watch and block
        stream_flow_run_logs(flow_run_id, max_duration=timedelta(minutes=1))


# def test_flow2_run_creation(self, client, flow2_id):
#     client.create_flow_run(flow_id=flow2_id)

# def test_flow3_run_creation(self, client, flow3_id):
#     client.create_flow_run(flow_id=flow3_id)
