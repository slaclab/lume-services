import os
import yaml
from datetime import datetime, timedelta
from pydantic import BaseModel, validator, Field
from prefect import Parameter
from prefect.backend.flow import FlowView
from typing import List, Optional, Dict, Literal, get_args
from prefect.tasks.prefect import (
    create_flow_run,
    wait_for_flow_run,
    get_task_run_result,
)
from prefect import Flow as PrefectFlow
from lume_services.services.scheduling.tasks import LoadDBResult

# Pydantic schema describing flow of flows composition


class ParameterNotInFlowError(Exception):
    def __init__(self, parameter_name: str, flow_name: str):
        self.flow_name = flow_name
        self.parameter_name = parameter_name
        self.message = "Parameter %s not in flow %s."
        super().__init__(self.message, self.parameter_name, self.flow_name)


class ParentFlowNotInFlowsError(Exception):
    def __init__(self, flow_name: str, flows: List[str]):
        self.flow_name = flow_name
        self.flows = flows
        self.message = "Parent flow %s not in flows: %s"
        super().__init__(self.message, self.flow_name, ", ".join(self.flows))


class TaskNotInFlowError(Exception):
    def __init__(self, flow_name: str, task_name: str):
        self.flow_name = flow_name
        self.task_name = task_name
        self.message = "Task %s not in flow %s."
        super().__init__(self.message, self.task_name, self.flow_name)


class MappedParameter(BaseModel):
    """There are three types of mapped parameters: file, db, and raw.

    file: File parameters are file outputs that will be loaded in downstream flows.
    Downstream loading must use the packaged `load_file` task in
    `lume_services.services.scheduling.tasks.file`.

    db: Database results ...

    raw: Raw values are passed from task output to parameter input.



    """

    parent_flow_name: str
    parent_task_name: str
    map_type: Literal["file", "db", "raw"] = "raw"


class RawMappedParameter(MappedParameter):
    map_type: str = Field("raw", const=True)


class FileMappedParameter(MappedParameter):
    map_type: str = Field("file", const=True)


class DBMappedParameter(MappedParameter):
    map_type: str = Field("db", const=True)
    attribute: str
    attribute_index: Optional[List[str]]


_string_to_mapped_parameter_type = {
    "db": DBMappedParameter,
    "file": FileMappedParameter,
    "raw": RawMappedParameter,
}


def _get_mapped_parameter_type(map_type: str):

    if map_type not in _string_to_mapped_parameter_type:
        raise ValueError("No mapped parameter type available for %s", map_type)

    return _string_to_mapped_parameter_type.get(map_type)


class Flow(BaseModel):
    name: str
    project_name: str
    parameters: Optional[Dict[str, Parameter]]
    mapped_parameters: Optional[Dict[str, MappedParameter]]
    prefect_flow: Optional[PrefectFlow]
    task_slugs: Optional[Dict[str, str]]
    labels: List[str] = ["lume-services"]

    class Config:
        arbitrary_types_allowed = True

    @validator("mapped_parameters", pre=True)
    def validate_mapped_parameters(cls, v):

        if v is None:
            return v

        mapped_parameters = {}

        for param_name, param in v.items():
            # persist instantiated params
            if isinstance(param, (MappedParameter,)):
                mapped_parameters[param_name] = param

            elif isinstance(param, (dict,)):
                # default raw
                if not param.get("map_type"):
                    mapped_parameters[param_name] = RawMappedParameter(**param)

                else:
                    mapped_param_type = _get_mapped_parameter_type(param["map_type"])
                    mapped_parameters[param_name] = mapped_param_type(**param)

            else:
                raise ValueError(
                    "Mapped parameters must be passed as instantiated \
                    MappedParameters or dictionary"
                )

        return mapped_parameters

    def load(self):
        flow = FlowView.from_flow_name(
            self.name, project_name=self.project_name, last_updated=True
        ).flow

        # assign attributes
        self.prefect_flow = flow
        self.task_slugs = {task.name: task.slug for task in flow.get_tasks()}
        self.parameters = {parameter.name: parameter for parameter in flow.parameters()}


class FlowConfig(BaseModel):
    image: Optional[str]
    env: Optional[List[str]]


class FlowRunConfig(BaseModel):
    flow: Optional[Flow]
    #   parameters: ...
    #   run_config: RunConfig
    #   wait: ...
    #   new_flow_context: ...
    run_name: str = None
    scheduled_start_time: datetime = None
    poll_interval: timedelta = timedelta(seconds=10)


class FlowOfFlows(BaseModel):
    name: str
    project_name: str
    composing_flows: dict
    prefect_flow: Optional[PrefectFlow]

    class Config:
        arbitrary_types_allowed = True

    @validator("composing_flows", pre=True)
    def validate(cls, v: List[dict]):
        """Validate composing flow data against Prefect server."""
        flows = {}

        # validate composing flow existence
        for flow in v:

            # compose flow objects
            flow_obj = Flow(
                name=flow["name"],
                project_name=flow["project_name"],
                mapped_parameters=flow.get("mapped_parameters"),
            )

            # load Prefect parameters
            flow_obj.load()
            flows[flow["name"]] = flow_obj

        # validate flow parameters
        for flow_name, flow in flows.items():
            if flow.mapped_parameters is not None:
                for parameter_name, parameter in flow.mapped_parameters.items():

                    # validate parameter is in flow spec
                    parameter_obj = flow.parameters.get(parameter_name)
                    if parameter_obj is None:
                        raise ParameterNotInFlowError(parameter_name, flow_name)

                    # validate parent flow is included in listed flows
                    parent_flow = flows.get(parameter.parent_flow_name)
                    if parent_flow is None:
                        raise ParentFlowNotInFlowsError(
                            parameter.parent_flow_name, list(flows.keys())
                        )

                    # validate task is in the parent flow
                    task = parent_flow.task_slugs.get(parameter.parent_task_name)

                    if task is None:
                        raise TaskNotInFlowError(
                            parameter.parent_flow_name, parameter.parent_task_name
                        )

        return flows

    def compose(self) -> PrefectFlow:
        """Compose Prefect flow from FlowOfFlows object.

        Returns:
            PrefectFlow

        """

        # compose flow of flows
        with PrefectFlow(self.name) as flow_of_flows:

            flow_runs = {}
            flow_waits = {}
            params = {}

            for i, (flow_name, flow) in enumerate(self.composing_flows.items()):

                # begin by creating parameters for all flow parameters
                flow_params = {}
                for param_name, param in flow.parameters.items():
                    # do not register mapped parameters as flow parameters
                    if (
                        flow.mapped_parameters is not None
                        and param_name in flow.mapped_parameters
                    ):
                        continue

                    # update name and slug
                    param.name = f"{flow_name}-{param_name}"
                    param.slug = f"{flow_name}-{param_name}"
                    params[param.name] = param

                    # use original param name for flow config
                    flow_params[param_name] = param

                # set up entry task
                if i == 0:
                    flow_run = create_flow_run(
                        flow_name=flow_name,
                        project_name=flow.project_name,
                        parameters=flow_params,
                        labels=flow.labels,
                    )

                # setup other tasks
                elif i > 0:

                    # create references to parameters
                    upstream_flows = set()
                    if flow.mapped_parameters is not None:

                        # update flow_params with mapping
                        for param_name, mapped_param in flow.mapped_parameters.items():
                            task_slug = self.composing_flows[
                                mapped_param.parent_flow_name
                            ].task_slugs[mapped_param.parent_task_name]

                            task_run_result = get_task_run_result(
                                flow_runs[mapped_param.parent_flow_name], task_slug
                            )

                            if mapped_param.map_type in ["raw", "file"]:
                                flow.prefect_flow.replace(
                                    flow_params[param_name], task_run_result
                                )

                            elif mapped_param.map_type == "db":
                                load_db_result = LoadDBResult()
                                db_result = load_db_result(
                                    task_run_result,
                                    mapped_param.attribute,
                                    attribute_index=mapped_param.attribute_index,
                                )
                                flow.prefect_flow.replace(
                                    flow_params[param_name], db_result
                                )

                                for param in load_db_result:
                                    flow.add_task(param)
                                    flow.add_edge(param, load_db_result, mapped=True)

                            else:
                                # should never reach if instantiating MappedParameter
                                mapped_param_types = get_args(
                                    MappedParameter.__fields__["map_type"].type_
                                )
                                raise ValueError(
                                    f"Task type {mapped_param.map_type} not in task. \
                                        Allowed types: {mapped_param_types}."
                                )

                            # add flow to upstream
                            upstream_flows.add(mapped_param.parent_flow_name)

                        flow_run = create_flow_run(
                            flow_name=flow_name,
                            project_name=flow.project_name,
                            parameters=flow_params,
                            labels=flow.labels,
                            raise_final_state=True,
                        )

                    # configure upstreams if any
                    for upstream in upstream_flows:
                        flow_run.set_upstream(flow_waits[upstream])

                flow_wait = wait_for_flow_run(flow_run, raise_final_state=True)
                flow_runs[flow_name] = flow_run
                flow_waits[flow_name] = flow_wait

        # validate flow of flows
        flow_of_flows.validate()

        # assign to obj
        self.prefect_flow = flow_of_flows

        # flow_id = flow_of_flows.register(project_name=self.project_name)
        return flow_of_flows

    def compose_and_register(self):
        """Compose flow and register with project.

        Returns:
            str: Registered flow id

        """

        flow = self.compose()
        flow_id = flow.register(self.project_name)
        return flow_id

    def compose_local(self):
        """

        Note:
            Prefect 1.0 does not allow subflow run without previous registration with
            the server. This function is a workaround, but will be massively simplified
            once moved to Prefect 2.0, which does support direct subflow run.
        """
        ...


def build_parameters(task, prefix: str = None):
    """

    Args:
        task: Task for which to build params
        prefix (str): Prefix to add to parameter names

    """

    params = {}

    for input_name, input in task.inputs.items():
        if not prefix:
            params[input_name] = Parameter(
                name=input_name, default=input["default"], required=input["required"]
            )
        else:
            params[f"{prefix}{input_name}"] = Parameter(
                name=f"{prefix}{input_name}",
                default=input["default"],
                required=input["required"],
            )

    return params


def _get_task_slugs_from_name(flow, name):

    return flow.get_tasks(name)


def _get_task_slugs_from_run_name(flow_run, name):
    return [
        task.task_slug for task in flow_run.get_all_task_runs() if task.name == name
    ]


def load_flow_of_flows_from_yaml(yaml_obj):

    if os.path.exists(yaml_obj):
        flow_of_flow_config = yaml.safe_load(open(yaml_obj))

    else:
        flow_of_flow_config = yaml_obj

    # now validate
    return FlowOfFlows(**flow_of_flow_config)
