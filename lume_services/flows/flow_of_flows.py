import os
import yaml
from pydantic import BaseModel, validator
from typing import List, Optional, get_args
from prefect.tasks.prefect import (
    create_flow_run,
    wait_for_flow_run,
    get_task_run_result,
)
from prefect import Flow as PrefectFlow
from lume_services.flows.flow import Flow, MappedParameter
from lume_services.services.scheduling.tasks import LoadDBResult


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

    @classmethod
    def from_yaml(cls, yaml_obj):
        if os.path.exists(yaml_obj):
            flow_of_flow_config = yaml.safe_load(open(yaml_obj))

        else:
            flow_of_flow_config = yaml_obj

        # now validate
        return cls(**flow_of_flow_config)
