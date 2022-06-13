import pytest
from pkg_resources import resource_filename
from prefect import Flow, task, Client, Parameter
from prefect.engine.results import LocalResult
from lume_services.scheduling.scheduling_service import load_flow_of_flows_from_yaml


@pytest.fixture(scope="session", autouse=True)
def flow_of_flows_yaml():
    return resource_filename(
        "lume_services.tests.scheduling.files", "flow_of_flows.yaml"
    )


@task(result=LocalResult(location="{flow_name}/{task_name}.prefect"))
def multiply(x, y):
    return x * y


@task(result=LocalResult(location="{flow_name}/{task_name}.prefect"))
def add(x, y):
    return x + y


with Flow("flow1") as flow1:
    parameter_1 = Parameter("parameter_1")
    parameter_2 = Parameter("parameter2")
    multiply(parameter_1, parameter_2)

with Flow("flow2") as flow2:
    parameter_1 = Parameter("parameter_1")
    parameter_2 = Parameter("parameter_2")
    add(parameter_1, parameter_2)

with Flow("flow3") as flow3:
    parameter_1 = Parameter("parameter_1")
    parameter_2 = Parameter("parameter_2")
    multiply(parameter_1, parameter_2)

# @pytest.fixture(autouse=True, scope="session")
# def prefect_test_fixture():
#    with prefect_test_harness():

# register flows
#        client = Client()
#        client.create_project(project_name="test")
#        flow1.register("test")
#        flow2.register("test")
#        flow3.register("test")
#        yield


flow_of_flows_yaml = resource_filename(
    "lume_services.tests.scheduling.files", "flow_of_flows.yaml"
)


@task(result=LocalResult(location="{flow_name}/{task_name}.prefect"))
def multiply(x, y):
    return x * y


@task(result=LocalResult(location="{flow_name}/{task_name}.prefect"))
def add(x, y):
    return x + y


@task(result=LocalResult(location="{flow_name}/{task_name}.prefect"))
def subtract(x, y):
    return x - y


with Flow("flow1") as flow1:
    parameter_1 = Parameter("parameter_1")
    parameter_2 = Parameter("parameter_2")
    multiply(parameter_1, parameter_2)

with Flow("flow2") as flow2:
    parameter_1 = Parameter("parameter_1")
    parameter_2 = Parameter("parameter_2")
    add(parameter_1, parameter_2)

with Flow("flow3") as flow3:
    parameter_1 = Parameter("parameter_1")
    parameter_2 = Parameter("parameter_2")
    subtract(parameter_1, parameter_2)
